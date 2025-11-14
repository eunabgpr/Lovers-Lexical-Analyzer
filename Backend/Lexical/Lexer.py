# Backend/Lexical/lexer.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable, List, Optional

from .Literals import Literals
from .Delims import valid_delimiters_identifier

RESERVED_WORDS = {
    "give": ("KEYWORD_IO_GIVE", "give"),
    "express": ("KEYWORD_IO_EXPRESS", "express"),
    "overshare": ("KEYWORD_IO_OVERSHARE", "overshare"),
    "dear": ("KEYWORD_TYPE_INT", "dear"),
    "dearest": ("KEYWORD_TYPE_FLOAT", "dearest"),
    "rant": ("KEYWORD_TYPE_STRING", "rant"),
    "status": ("KEYWORD_TYPE_BOOL", "bostatusol"),
    "forever": ("KEYWORD_IF", "forever"),
    "more": ("KEYWORD_ELSE", "more"),
    "forevermore": ("KEYWORD_ELSEIF", "forevermore"),
    "choose": ("KEYWORD_SWITCH", "choose"),
    "phase": ("KEYWORD_CASE", "phase"),
    "bareminimum": ("KEYWORD_DEFAULT", "bareminimum"),
    "for": ("KEYWORD_FOR", "for"),
    "while": ("KEYWORD_WHILE", "while"),
    "pursue": ("KEYWORD_DO_WHILE", "pursue"),
    "breakup": ("KEYWORD_BREAK", "breakup"),
    "moveon": ("KEYWORD_CONTINUE", "moveon"),
    "love": ("KEYWORD_MAIN", "love"),
    "periodt": ("KEYWORD_ENDL", "periodt"),
    "const": ("KEYWORD_CONST", "const"),
    "redflag": ("BOOL_LITERAL_FALSE", "redflag"),
    "greenflag": ("BOOL_LITERAL_TRUE", "greenflag"),
    "boundaries": ("KEYWORD_NAMESPACE", "boundaries"),
    "comeback": ("KEYWORD_RETURN", "comeback"),
}

MULTI_CHAR_OPERATORS = {
    "==": "OP_EQ",
    "!=": "OP_NEQ",
    ">=": "OP_GTE",
    "<=": "OP_LTE",
    "&&": "OP_AND",
    "||": "OP_OR",
    "++": "OP_INC",
    "--": "OP_DEC",
    "+=": "OP_PLUS_ASSIGN",
    "-=": "OP_MINUS_ASSIGN",
    "*=": "OP_MUL_ASSIGN",
    "/=": "OP_DIV_ASSIGN",
    "%=": "OP_MOD_ASSIGN",
    "::": "OP_SCOPE",
    "->": "OP_ARROW",
}

SINGLE_CHAR_TOKENS = {
    ";": "SEMICOLON",
    ",": "COMMA",
    "(": "LPAREN",
    ")": "RPAREN",
    "{": "LBRACE",
    "}": "RBRACE",
    "[": "LBRACKET",
    "]": "RBRACKET",
    ":": "COLON",
    "?": "QUESTION",
    ".": "DOT",
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    "%": "PERCENT",
    "=": "ASSIGN",
    ">": "GT",
    "<": "LT",
    "!": "BANG",
    "&": "AMPERSAND",
    "|": "PIPE",
    "#": "HASH",
}

IDENTIFIER_DELIMS = set(valid_delimiters_identifier)
ALPHA = Literals["alphabet"]
DIGIT = Literals["digit"]
ALNUM = Literals["alphanumeric"]
WHITESPACE = {" ", "\r", "\t", "\f"}

@dataclass
class Token:
    kind: str
    lexeme: str
    literal: Optional[str] = None
    line: int = 1
    column: int = 1
    cpp_equivalent: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

class LexerError(Exception):
    pass

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.length = len(source)
        self.start = 0
        self.pos = 0
        self.line = 1
        self.column = 1

    def scan_tokens(self) -> List[Token]:
        tokens: List[Token] = []
        while not self._is_at_end():
            self.start = self.pos
            start_line, start_col = self.line, self.column
            ch = self._advance()

            if ch in WHITESPACE:
                continue
            if ch == "\n":
                tokens.append(
                    Token("NEWLINE", "\\n", line=start_line, column=start_col)
                )
                continue
            if ch == "/" and self._match("/"):
                self._skip_line_comment()
                continue
            if ch == "/" and self._match("*"):
                self._skip_block_comment()
                continue
            if ch in {"'", '"'}:
                tokens.append(self._string_token(ch, start_line, start_col))
                continue
            if ch.isdigit():
                tokens.append(self._number_token(start_line, start_col))
                continue
            if self._is_identifier_start(ch):
                tokens.append(self._identifier_token(start_line, start_col))
                continue

            two_char = ch + self._peek()
            if two_char in MULTI_CHAR_OPERATORS:
                self._advance()
                tokens.append(
                    Token(MULTI_CHAR_OPERATORS[two_char], two_char, line=start_line, column=start_col)
                )
                continue

            if ch in SINGLE_CHAR_TOKENS:
                tokens.append(Token(SINGLE_CHAR_TOKENS[ch], ch, line=start_line, column=start_col))
                continue

            raise LexerError(f"Unexpected character {ch!r} at {start_line}:{start_col}")

        tokens.append(Token("EOF", "", line=self.line, column=self.column))
        return tokens

    # --- helpers -----------------------------------------------------------

    def _identifier_token(self, line: int, col: int) -> Token:
        while self._is_identifier_part(self._peek()):
            self._advance()
        lexeme = self.source[self.start:self.pos]
        entry = RESERVED_WORDS.get(lexeme)
        if entry:
            kind, cpp_equiv = entry
            literal = cpp_equiv if kind.startswith("BOOL_LITERAL") else None
            return Token(kind="KEYWORD" if kind.startswith("KEYWORD") else kind,
                         lexeme=lexeme,
                         literal=literal,
                         line=line,
                         column=col,
                         cpp_equivalent=cpp_equiv)
        return Token("IDENTIFIER", lexeme, line=line, column=col)

    def _number_token(self, line: int, col: int) -> Token:
        while self._peek().isdigit():
            self._advance()
        token_kind = "INT_LITERAL"
        if self._peek() == "." and self._peek_next().isdigit():
            token_kind = "FLOAT_LITERAL"
            self._advance()
            while self._peek().isdigit():
                self._advance()
        lexeme = self.source[self.start:self.pos]
        return Token(token_kind, lexeme, literal=lexeme, line=line, column=col)

    def _string_token(self, quote: str, line: int, col: int) -> Token:
        escaped = False
        while not self._is_at_end():
            c = self._advance()
            if escaped:
                escaped = False
                continue
            if c == "\\":
                escaped = True
                continue
            if c == quote:
                lexeme = self.source[self.start:self.pos]
                inner = lexeme[1:-1]
                kind = "CHAR_LITERAL" if quote == "'" and len(inner) == 1 else "STRING_LITERAL"
                return Token(kind, lexeme, literal=inner, line=line, column=col)
            if c == "\n":
                raise LexerError(f"Unterminated string at {line}:{col}")
        raise LexerError(f"Unterminated string at {line}:{col}")

    def _skip_line_comment(self) -> None:
        while not self._is_at_end() and self._peek() != "\n":
            self._advance()

    def _skip_block_comment(self) -> None:
        while not self._is_at_end():
            if self._peek() == "*" and self._peek_next() == "/":
                self._advance()
                self._advance()
                return
            self._advance()
        raise LexerError("Unterminated block comment")

    def _is_identifier_start(self, ch: str) -> bool:
        return ch in ALPHA or ch == "_"

    def _is_identifier_part(self, ch: str) -> bool:
        return ch in ALNUM or ch == "_"

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self.source[self.pos]

    def _peek_next(self) -> str:
        if self.pos + 1 >= self.length:
            return "\0"
        return self.source[self.pos + 1]

    def _match(self, expected: str) -> bool:
        if self._is_at_end() or self.source[self.pos] != expected:
            return False
        self.pos += 1
        self.column += 1
        return True

    def _is_at_end(self) -> bool:
        return self.pos >= self.length

def tokenize(source: str) -> List[Token]:
    return Lexer(source).scan_tokens()

def _format_tokenizer(tok: Token) -> str:
    if tok.cpp_equivalent:
        return tok.cpp_equivalent
    if tok.literal is not None:
        return tok.literal
    return tok.lexeme


def tokens_as_rows(tokens: Iterable[Token]) -> List[dict]:
    rows: List[dict] = []
    for tok in tokens:
        if tok.kind == "EOF":
            continue
        rows.append(
            {
                "lexeme": tok.lexeme,
                "token": tok.kind,
                "tokenizer": _format_tokenizer(tok),
            }
        )
    return rows
