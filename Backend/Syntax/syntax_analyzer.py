"""
Stage 1 parser: consumes lexer tokens and performs structural/syntax validation.
Implements:
- Program shape: optional boundaries/global decls, then required `love main() { ... }`.
- Declarations (with multi-declarators, array dims, optional initializers).
- Function definitions.
- Expression parsing with precedence.
- Blocks with declarations and expression statements.
- Multi-error reporting with simple synchronization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Tuple

from Backend.Lexical import Lexer, tokens_as_rows
from Backend.Lexical.Lexer import LexerError, Token  # type: ignore
from Backend.Syntax.syntax_errors import make_error


# --- Token stream -----------------------------------------------------------


class TokenStream:
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def at_end(self) -> bool:
        return self.peek().kind == "EOF"

    def advance(self) -> Token:
        if not self.at_end():
            self.pos += 1
        return self.tokens[self.pos - 1]

    def match(self, *kinds: str) -> bool:
        if self.peek().kind in kinds:
            self.advance()
            return True
        return False

    def expect(self, kinds: List[str]) -> Optional[Token]:
        if self.peek().kind in kinds:
            return self.advance()
        return None


# --- Errors -----------------------------------------------------------------

@dataclass
class ParseError:
    message: str
    line: int
    column: int
    expected: List[str]
    token: Optional[Token] = None

    def to_payload(self) -> dict:
        tok = self.token
        return {
            "ok": False,
            "message": self.message,
            "code": "ERR_SYNTAX",
            "expected": self.expected,
            "token": {
                "lexeme": tok.lexeme if tok else "",
                "kind": tok.kind if tok else "EOF",
                "line": self.line,
                "column": self.column,
            },
        }


# --- Parser -----------------------------------------------------------------


class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self.ts = TokenStream(tokens)
        self.errors: List[ParseError] = []

    def parse(self) -> Tuple[bool, Any]:
        try:
            self.program()
        except Exception:
            # Defensive: any unexpected exception becomes a syntax error.
            if not self.errors:
                tok = self.ts.peek()
                self.errors.append(
                    ParseError(
                        "Unexpected parser error.",
                        tok.line,
                        tok.column,
                        [],
                        tok,
                    )
                )
        if self.errors:
            first = self.errors[0]
            return False, {
                "ok": False,
                "message": first.message,
                "code": "ERR_SYNTAX",
                "expected": first.expected,
                "token": first.to_payload().get("token"),
                "errors": [make_error(e.message, e.token, e.expected) for e in self.errors],
            }
        return True, tokens_as_rows(self.ts.tokens)

    # Grammar: program -> boundaries_opt globals love_main
    def program(self) -> None:
        self.skip_newlines()
        self.boundaries_opt()
        self.globals()
        self.love_main()
        self.skip_newlines()
        if not self.ts.at_end():
            tok = self.ts.peek()
            self.error(tok, "Unexpected tokens after program end", [])

    def boundaries_opt(self) -> None:
        if self.ts.peek().lexeme == "boundaries":
            self.ts.advance()
            if not self.ts.match("IDENTIFIER"):
                self.error(self.ts.peek(), "Expected identifier after boundaries", ["IDENTIFIER"])
            if not self.ts.match("LBRACE"):
                self.error(self.ts.peek(), "Expected '{' after boundaries name", ["{"])
            self.globals()
            if not self.ts.match("RBRACE"):
                self.error(self.ts.peek(), "Expected '}' after boundaries block", ["}"])

    def globals(self) -> None:
        while not self.ts.at_end() and self.ts.peek().lexeme != "love":
            self.skip_newlines()
            if self.ts.at_end() or self.ts.peek().lexeme == "love":
                break
            if not self.declaration_or_function():
                # Synchronize on ';' or '}'.
                self.synchronize()

    def love_main(self) -> None:
        tok = self.ts.peek()
        if tok.lexeme != "love":
            self.error(tok, "Program must start with `love` block", ["love"])
            return
        self.ts.advance()
        if not self.ts.match("IDENTIFIER"):
            self.error(self.ts.peek(), "Expected identifier after `love`", ["IDENTIFIER"])
        if not self.ts.match("LPAREN"):
            self.error(self.ts.peek(), "Expected '(' after main name", ["("])
        if not self.ts.match("RPAREN"):
            self.error(self.ts.peek(), "Expected ')' after parameters", [")"])
        self.block()

    def declaration_or_function(self) -> bool:
        tok = self.ts.peek()
        if not tok.kind.startswith("KEYWORD_TYPE"):
            return False
        # lookahead to see if function: type IDENTIFIER '('
        if self._lookahead_is_function():
            self.function_def()
        else:
            self.declaration()
        return True

    def _lookahead_is_function(self) -> bool:
        # type IDENTIFIER '('
        save = self.ts.pos
        self.ts.advance()  # type
        is_func = self.ts.match("IDENTIFIER") and self.ts.match("LPAREN")
        self.ts.pos = save
        return is_func

    def function_def(self) -> None:
        self.ts.advance()  # return type
        if not self.ts.match("IDENTIFIER"):
            self.error(self.ts.peek(), "Expected function name", ["IDENTIFIER"])
        self.param_list()
        self.block()

    def param_list(self) -> None:
        if not self.ts.match("LPAREN"):
            self.error(self.ts.peek(), "Expected '(' in parameter list", ["("])
            return
        if self.ts.peek().kind.startswith("KEYWORD_TYPE"):
            self.param()
            while self.ts.match("COMMA"):
                self.param()
        if not self.ts.match("RPAREN"):
            self.error(self.ts.peek(), "Expected ')' to close parameters", [")"])

    def param(self) -> None:
        self.ts.advance()  # type
        if not self.ts.match("IDENTIFIER"):
            self.error(self.ts.peek(), "Expected parameter name", ["IDENTIFIER"])
        self.array_decl()

    def declaration(self) -> None:
        self.ts.advance()  # type
        self.declarator()
        while self.ts.match("COMMA"):
            self.declarator()
        if not self.ts.match("SEMICOLON"):
            self.error(self.ts.peek(), "Expected ';' after declaration", [";"])

    def declarator(self) -> None:
        if not self.ts.match("IDENTIFIER"):
            self.error(self.ts.peek(), "Expected identifier in declaration", ["IDENTIFIER"])
            return
        self.array_decl()
        if self.ts.match("ASSIGN"):
            self.expr()

    def array_decl(self) -> None:
        while self.ts.match("LBRACKET"):
            if not self.ts.match("RBRACKET"):
                if not self.ts.peek().kind in {"INT_LITERAL", "IDENTIFIER"}:
                    self.error(self.ts.peek(), "Expected array size or ']'", ["]", "INT_LITERAL", "IDENTIFIER"])
                else:
                    self.expr()
                if not self.ts.match("RBRACKET"):
                    self.error(self.ts.peek(), "Expected ']'", ["]"])

    def block(self) -> None:
        if not self.ts.match("LBRACE"):
            self.error(self.ts.peek(), "Expected '{' to start block", ["{"])
            return
        while not self.ts.at_end():
            self.skip_newlines()
            if self.ts.peek().kind == "RBRACE":
                break
            if self.ts.peek().kind.startswith("KEYWORD_TYPE"):
                self.declaration()
            else:
                self.statement()
        if not self.ts.match("RBRACE"):
            self.error(self.ts.peek(), "Expected '}' to close block", ["}"])

    def statement(self) -> None:
        self.skip_newlines()
        # I/O statements
        tok = self.ts.peek()
        if tok.kind == "KEYWORD_IO_GIVE":
            self.input_statement()
            return
        if tok.kind == "KEYWORD_IO_EXPRESS":
            self.output_statement()
            return
        if tok.kind == "KEYWORD_IO_OVERSHARE":
            self.overshare_statement()
            return
        if tok.kind == "KEYWORD_IF":  # forever
            self.conditional_statement()
            return
        if tok.kind in {"KEYWORD_FOR", "KEYWORD_WHILE", "KEYWORD_DO_WHILE"}:
            self.loop_state()
            return
        if tok.kind == "KEYWORD_SWITCH":  # choose
            self.choose_state()
            return
        if tok.kind in {"KEYWORD_BREAK", "KEYWORD_CONTINUE"}:
            self.control_flow_statement()
            return
        if tok.kind == "KEYWORD_RETURN":
            self.comeback_statement()
            return

        # Expression statement
        self.expr()
        self.skip_newlines()
        if not self.ts.match("SEMICOLON"):
            self.error(self.ts.peek(), "Expected ';' after statement", [";", "}"])

    # --- Expressions with precedence ---------------------------------------

    def expr(self) -> None:
        self.assignment()

    def assignment(self) -> None:
        self.logical_or()
        if self.ts.peek().kind in {"ASSIGN", "OP_PLUS_ASSIGN", "OP_MINUS_ASSIGN", "OP_MUL_ASSIGN", "OP_DIV_ASSIGN", "OP_MOD_ASSIGN"}:
            self.ts.advance()
            self.assignment()

    def logical_or(self) -> None:
        self.logical_and()
        while self.ts.peek().kind in {"OP_OR"}:
            self.ts.advance()
            self.logical_and()

    def logical_and(self) -> None:
        self.equality()
        while self.ts.peek().kind in {"OP_AND"}:
            self.ts.advance()
            self.equality()

    def equality(self) -> None:
        self.comparison()
        while self.ts.peek().kind in {"OP_EQ", "OP_NEQ"}:
            self.ts.advance()
            self.comparison()

    def comparison(self) -> None:
        self.term()
        while self.ts.peek().kind in {"GT", "LT", "OP_GTE", "OP_LTE"}:
            self.ts.advance()
            self.term()

    def term(self) -> None:
        self.factor()
        while self.ts.peek().kind in {"PLUS", "MINUS"}:
            self.ts.advance()
            self.factor()

    def factor(self) -> None:
        self.unary()
        while self.ts.peek().kind in {"STAR", "SLASH", "PERCENT"}:
            self.ts.advance()
            self.unary()

    def unary(self) -> None:
        if self.ts.peek().kind in {"BANG", "MINUS", "OP_INC", "OP_DEC"}:
            self.ts.advance()
            self.unary()
        else:
            self.primary()

    def primary(self) -> None:
        tok = self.ts.peek()
        if tok.kind in {"IDENTIFIER", "INT_LITERAL", "FLOAT_LITERAL", "STRING_LITERAL", "BOOL_LITERAL_FALSE", "BOOL_LITERAL_TRUE"}:
            self.ts.advance()
            self.postfix()
            return
        if tok.kind == "LPAREN":
            self.ts.advance()
            self.expr()
            if not self.ts.match("RPAREN"):
                self.error(self.ts.peek(), "Expected ')' after expression", [")"])
            return
        self.error(tok, "Expected expression", ["IDENTIFIER", "LITERAL", "("])
        self.ts.advance()

    # --- I/O statements ----------------------------------------------------

    def input_statement(self) -> None:
        # give >> expr ;
        self.ts.advance()  # give
        if not self.ts.match("OP_RSHIFT"):
            self.error(self.ts.peek(), "Expected '>>' after give", [">>"])
            return
        self.expr()
        self.skip_newlines()
        if not self.ts.match("SEMICOLON"):
            self.error(self.ts.peek(), "Expected ';' after input statement", [";"])

    def output_statement(self) -> None:
        # express << value (<< value)* ;
        self.ts.advance()  # express
        if not self.ts.match("OP_LSHIFT"):
            self.error(self.ts.peek(), "Expected '<<' after express", ["<<"])
            return
        self.output_chain()
        self.skip_newlines()
        if not self.ts.match("SEMICOLON"):
            self.error(self.ts.peek(), "Expected ';' after output statement", [";"])

    def output_chain(self) -> None:
        # value then zero or more << value
        self.output_value()
        while self.ts.match("OP_LSHIFT"):
            self.output_value()

    def output_value(self) -> None:
        tok = self.ts.peek()
        if tok.kind == "KEYWORD_ENDL":  # periodt
            self.ts.advance()
            return
        if tok.kind in {"IDENTIFIER", "INT_LITERAL", "FLOAT_LITERAL", "STRING_LITERAL", "BOOL_LITERAL_FALSE", "BOOL_LITERAL_TRUE"} or tok.kind == "LPAREN":
            self.expr()
            return
        self.error(tok, "Expected value after '<<'", ["IDENTIFIER", "LITERAL", "(", "periodt"])
        self.ts.advance()

    def overshare_statement(self) -> None:
        # overshare ( args ) ;
        self.ts.advance()  # overshare
        if not self.ts.match("LPAREN"):
            self.error(self.ts.peek(), "Expected '(' after overshare", ["("])
            return
        self.arguments()
        if not self.ts.match("RPAREN"):
            self.error(self.ts.peek(), "Expected ')' after overshare args", [")"])
        self.skip_newlines()
        if not self.ts.match("SEMICOLON"):
            self.error(self.ts.peek(), "Expected ';' after overshare", [";"])

    def arguments(self) -> None:
        if self.ts.peek().kind in {"RPAREN"}:
            return
        self.expr()
        while self.ts.match("COMMA"):
            self.expr()

    # --- Conditionals / loops / switch -------------------------------------

    def conditional_statement(self) -> None:
        # forever (cond) { body } [forevermore (cond){body}] [more {body}]
        self.ts.advance()  # forever
        if not self.ts.match("LPAREN"):
            self.error(self.ts.peek(), "Expected '(' after forever", ["("])
        else:
            self.expr()
            if not self.ts.match("RPAREN"):
                self.error(self.ts.peek(), "Expected ')' after condition", [")"])
        self.block()
        while self.ts.peek().kind == "KEYWORD_ELSEIF":
            self.ts.advance()
            if not self.ts.match("LPAREN"):
                self.error(self.ts.peek(), "Expected '(' after forevermore", ["("])
            else:
                self.expr()
                if not self.ts.match("RPAREN"):
                    self.error(self.ts.peek(), "Expected ')' after condition", [")"])
            self.block()
        if self.ts.peek().kind == "KEYWORD_ELSE":
            self.ts.advance()
            self.block()

    def loop_state(self) -> None:
        kind = self.ts.peek().kind
        if kind == "KEYWORD_FOR":
            self.ts.advance()
            if not self.ts.match("LPAREN"):
                self.error(self.ts.peek(), "Expected '(' after for", ["("])
            else:
                # init
                if self.ts.peek().kind.startswith("KEYWORD_TYPE"):
                    self.declaration()
                else:
                    self.expr()
                    if not self.ts.match("SEMICOLON"):
                        self.error(self.ts.peek(), "Expected ';' after for init", [";"])
                # condition
                self.expr()
                if not self.ts.match("SEMICOLON"):
                    self.error(self.ts.peek(), "Expected ';' after for condition", [";"])
                # update
                self.expr()
                if not self.ts.match("RPAREN"):
                    self.error(self.ts.peek(), "Expected ')' after for update", [")"])
            self.block()
        elif kind == "KEYWORD_WHILE":
            self.ts.advance()
            if not self.ts.match("LPAREN"):
                self.error(self.ts.peek(), "Expected '(' after while", ["("])
            else:
                self.expr()
                if not self.ts.match("RPAREN"):
                    self.error(self.ts.peek(), "Expected ')' after condition", [")"])
            self.block()
        elif kind == "KEYWORD_DO_WHILE":
            self.ts.advance()
            self.block()
            if not self.ts.match("KEYWORD_WHILE"):
                self.error(self.ts.peek(), "Expected 'while' after pursue block", ["while"])
            else:
                if not self.ts.match("LPAREN"):
                    self.error(self.ts.peek(), "Expected '(' after while", ["("])
                else:
                    self.expr()
                    if not self.ts.match("RPAREN"):
                        self.error(self.ts.peek(), "Expected ')' after condition", [")"])
                if not self.ts.match("SEMICOLON"):
                    self.error(self.ts.peek(), "Expected ';' after pursue while", [";"])

    def choose_state(self) -> None:
        # choose (expr) { cases bareminimum? }
        self.ts.advance()
        if not self.ts.match("LPAREN"):
            self.error(self.ts.peek(), "Expected '(' after choose", ["("])
        else:
            self.expr()
            if not self.ts.match("RPAREN"):
                self.error(self.ts.peek(), "Expected ')' after choose expr", [")"])
        if not self.ts.match("LBRACE"):
            self.error(self.ts.peek(), "Expected '{' after choose", ["{"])
            return
        while self.ts.peek().lexeme == "phase":
            self.ts.advance()
            self.expr()
            if not self.ts.match("COLON"):
                self.error(self.ts.peek(), "Expected ':' after phase value", [":"])
            self.block()
        if self.ts.peek().lexeme == "bareminimum":
            self.ts.advance()
            if not self.ts.match("COLON"):
                self.error(self.ts.peek(), "Expected ':' after bareminimum", [":"])
            self.block()
        if not self.ts.match("RBRACE"):
            self.error(self.ts.peek(), "Expected '}' after choose cases", ["}"])

    def control_flow_statement(self) -> None:
        # breakup ; | moveon ;
        self.ts.advance()
        if not self.ts.match("SEMICOLON"):
            self.error(self.ts.peek(), "Expected ';' after control flow statement", [";"])

    def comeback_statement(self) -> None:
        self.ts.advance()
        if self.ts.peek().kind != "SEMICOLON":
            self.expr()
        if not self.ts.match("SEMICOLON"):
            self.error(self.ts.peek(), "Expected ';' after return", [";"])

    def postfix(self) -> None:
        while True:
            if self.ts.match("LPAREN"):
                while self.ts.peek().kind != "RPAREN" and not self.ts.at_end():
                    self.expr()
                    if not self.ts.match("COMMA"):
                        break
                if not self.ts.match("RPAREN"):
                    self.error(self.ts.peek(), "Expected ')' after arguments", [")"])
            elif self.ts.match("LBRACKET"):
                self.expr()
                if not self.ts.match("RBRACKET"):
                    self.error(self.ts.peek(), "Expected ']' after index", ["]"])
            else:
                break

    # --- Error handling ----------------------------------------------------

    def error(self, tok: Token, message: str, expected: List[str]) -> None:
        self.errors.append(ParseError(message, tok.line, tok.column, expected, tok))

    def synchronize(self) -> None:
        # skip until semicolon or closing brace
        while not self.ts.at_end():
            if self.ts.peek().kind in {"SEMICOLON", "RBRACE"}:
                self.ts.advance()
                return
            self.ts.advance()

    def skip_newlines(self) -> None:
        while not self.ts.at_end() and self.ts.peek().kind == "NEWLINE":
            self.ts.advance()


def analyze(
    code: str,
    pre_analyzed_tokens: Optional[Iterable[dict]] = None,
) -> Tuple[bool, Any]:
    if pre_analyzed_tokens is not None:
        tokens = list(pre_analyzed_tokens)
    else:
        try:
            tokens = Lexer(code).scan_tokens()
        except LexerError as exc:
            msg = str(exc)
            return False, {
                "ok": False,
                "type": "lexical",
                "message": msg,
                "expected": [],
                "token": None,
            }
        except Exception as exc:  # pragma: no cover - defensive
            return False, {
                "ok": False,
                "type": "lexical",
                "message": f"Lexing failed: {exc}",
                "expected": [],
                "token": None,
            }

    parser = Parser(tokens)
    return parser.parse()


if __name__ == "__main__":
    import sys

    src = sys.stdin.read()
    ok, payload = analyze(src)
    if ok:
        print("OK")
        for row in payload:
            print(row)
    else:
        print("ERROR")
        print(payload)
