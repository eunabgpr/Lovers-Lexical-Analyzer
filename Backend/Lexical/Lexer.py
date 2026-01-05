# Backend/Lexical/lexer.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation
from typing import Iterable, List, Optional

from .Literals import Literals
from .Delims import valid_delimiters_identifier
from Backend.Syntax.token_map import (
    expanded_reserved_word_follows,
    expanded_identifier_follows,
    expanded_reserved_symbol_follows,
)

RESERVED_WORDS = {
    "give": ("KEYWORD_IO_GIVE", "give"),
    "express": ("KEYWORD_IO_EXPRESS", "express"),
    "overshare": ("KEYWORD_IO_OVERSHARE", "overshare"),
    "dear": ("KEYWORD_TYPE_INT", "dear"),
    "dearest": ("KEYWORD_TYPE_FLOAT", "dearest"),
    "rant": ("KEYWORD_TYPE_STRING", "rant"),
    "status": ("KEYWORD_TYPE_BOOL", "status"),
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
    ">>": "OP_RSHIFT",
    "<<": "OP_LSHIFT",
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


TOKEN_TYPE_OVERRIDES: dict = {}

IDENTIFIER_DELIMS = set(valid_delimiters_identifier)
ALPHA = Literals["alphabet"]
DIGIT = Literals["digit"]
ALNUM = Literals["alphanumeric"]
WHITESPACE = {" ", "\r", "\t", "\f"}
DISALLOWED_IDENTIFIERS = {"true", "false"}
# Disallow only symbols that should never appear immediately after an identifier.
BAD_SYMBOLS_AFTER_IDENTIFIER = set("!@#$^|\\?~")
IDENT_FOLLOW_CHARS = (
    expanded_identifier_follows.get("variant_1", set())
    | expanded_identifier_follows.get("variant_2", set())
    | IDENTIFIER_DELIMS
    | WHITESPACE
    | {"\n", "\0"}
)

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
    def __init__(self, message: str, tokens: Optional[List["Token"]] = None):
        super().__init__(message)
        self.tokens = tokens or []

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.length = len(source)
        self.start = 0
        self.pos = 0
        self.line = 1
        self.column = 1
        self._partial_tokens: List[Token] = []

    def scan_tokens(self) -> List[Token]:
        tokens: List[Token] = []
        self._partial_tokens = tokens
        while not self._is_at_end():
            self.start = self.pos
            start_line, start_col = self.line, self.column
            ch = self._advance()
            self._scan_single_token(ch, tokens, start_line, start_col)

        tokens.append(Token("EOF", "", line=self.line, column=self.column))
        return tokens

    def scan_tokens_collect_errors(self) -> (List[Token], List[str]):
        tokens: List[Token] = []
        errors: List[str] = []
        self._partial_tokens = tokens
        while not self._is_at_end():
            self.start = self.pos
            start_line, start_col = self.line, self.column
            ch = self._advance()
            try:
                self._scan_single_token(ch, tokens, start_line, start_col)
            except LexerError as exc:
                errors.append(str(exc))
                self._recover_after_error()
                continue
        tokens.append(Token("EOF", "", line=self.line, column=self.column))
        return tokens, errors

    # --- single token scanner ----------------------------------------------

    def _scan_single_token(self, ch: str, tokens: List[Token], start_line: int, start_col: int) -> None:
        if ch in WHITESPACE:
            return
        if ch == "\n":
            tokens.append(Token("NEWLINE", "\\n", line=start_line, column=start_col))
            return
        if ch == "/" and self._match("/"):
            self._skip_line_comment()
            return
        if ch == "/" and self._match("*"):
            self._skip_block_comment()
            return
        if ch in {"'", '"'}:
            tokens.append(self._string_token(ch, start_line, start_col))
            return
        if ch.isdigit():
            tokens.append(self._number_token(start_line, start_col))
            return
        if self._is_identifier_start(ch):
            tokens.append(self._identifier_token(start_line, start_col))
            return

        two_char = ch + self._peek()
        if two_char in MULTI_CHAR_OPERATORS:
            self._advance()
            self._validate_symbol_follow(two_char, start_line, start_col)
            tokens.append(Token(MULTI_CHAR_OPERATORS[two_char], two_char, line=start_line, column=start_col))
            return

        if ch in SINGLE_CHAR_TOKENS:
            lexeme = ch
            self._validate_symbol_follow(lexeme, start_line, start_col)
            tokens.append(Token(SINGLE_CHAR_TOKENS[lexeme], lexeme, line=start_line, column=start_col))
            return

        raise LexerError(f"Unexpected character {ch!r} at {start_line}:{start_col}", tokens)

    def _recover_after_error(self) -> None:
        # Skip ahead until a likely delimiter/whitespace to continue scanning.
        self._advance() if not self._is_at_end() else None
        while not self._is_at_end():
            ch = self._peek()
            if ch in WHITESPACE or ch == "\n" or ch in IDENTIFIER_DELIMS:
                return
            self._advance()

    # --- helpers -----------------------------------------------------------

    def _identifier_token(self, line: int, col: int) -> Token:
        while self._is_identifier_part(self._peek()):
            self._advance()
        lexeme = self.source[self.start:self.pos]
        if len(lexeme) > 20:
            raise LexerError(
                f"Identifier `{lexeme}` exceeds the maximum length of 20 characters at {line}:{col}",
                self._partial_tokens,
            )
        nxt = self._peek()
        if nxt in BAD_SYMBOLS_AFTER_IDENTIFIER:
            if nxt == "!" and self._peek_next() == "=":
                pass  # allow '!='
            elif nxt == "|" and self._peek_next() == "|":
                pass  # allow '||'
            else:
                raise LexerError(
                    f"Invalid delimiter `{nxt}` after identifier `{lexeme}` at {line}:{col}\n\nExpected: {self._format_expected(IDENT_FOLLOW_CHARS)}",
                    self._partial_tokens,
                )
        entry = RESERVED_WORDS.get(lexeme)
        if entry is None:
            lowered = lexeme.lower()
            if lowered in DISALLOWED_IDENTIFIERS:
                raise LexerError(
                    f"`{lexeme}` is not valid in this language; use `greenflag` or `redflag` at {line}:{col}",
                    self._partial_tokens,
                )
            if lowered in RESERVED_WORDS:
                raise LexerError(
                    f"Reserved word `{lowered}` must be written in lowercase at {line}:{col}",
                    self._partial_tokens,
                )
        if entry:
            nxt = self._peek()
            allowed = expanded_reserved_word_follows.get(lexeme, IDENT_FOLLOW_CHARS)
            if nxt not in allowed:
                raise LexerError(
                    f"Reserved word `{lexeme}` must be followed by a delimiter at {line}:{col}\n\nExpected: {self._format_expected(allowed)}",
                    self._partial_tokens,
                )
            kind, cpp_equiv = entry
            literal = cpp_equiv if kind.startswith("BOOL_LITERAL") else None
            return Token(kind=kind,
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
        nxt = self._peek()
        if nxt not in IDENT_FOLLOW_CHARS:
            tok = Token(token_kind, lexeme, literal=lexeme, line=line, column=col)
            self._partial_tokens.append(tok)
            human_kind = "float" if token_kind == "FLOAT_LITERAL" else "integer"
            raise LexerError(
                f"Invalid delimiter after {human_kind} {lexeme}: {nxt} at {line}:{self.column}\nExpected: {self._format_expected(IDENT_FOLLOW_CHARS)}",
                self._partial_tokens,
            )
        if token_kind == "INT_LITERAL":
            # Enforce dear literal rules: max 10 digits (ignoring leading zeros) and max value 9999999999.
            digits_only = lexeme.lstrip("0") or "0"
            if len(digits_only) > 10:
                raise LexerError(
                    f"Integer literal `{lexeme}` exceeds maximum length of 10 digits at {line}:{col}",
                    self._partial_tokens,
                )
            value = int(digits_only)
            if value > 9999999999:
                raise LexerError(
                    f"Integer literal `{lexeme}` exceeds maximum value 9999999999 at {line}:{col}",
                    self._partial_tokens,
                )
            return Token(token_kind, lexeme, literal=lexeme, line=line, column=col)

        # FLOAT_LITERAL: dearest rules
        int_part, _, frac_part = lexeme.partition(".")
        norm_int = int_part.lstrip("0") or "0"
        norm_frac_raw = frac_part.rstrip("0")
        truncated_frac = norm_frac_raw[:6] if norm_frac_raw else "0"

        if len(norm_int) > 10:
            raise LexerError(
                f"Float literal `{lexeme}` exceeds 10 digits before decimal at {line}:{col}",
                self._partial_tokens,
            )
        if len(norm_int) + len(truncated_frac) > 16:
            raise LexerError(
                f"Float literal `{lexeme}` exceeds 16 total digits at {line}:{col}",
                self._partial_tokens,
            )
        try:
            numeric_val = Decimal(f"{norm_int}.{truncated_frac}")
        except (InvalidOperation, ValueError):
            raise LexerError(
                f"Invalid float literal `{lexeme}` at {line}:{col}",
                self._partial_tokens,
            )
        if numeric_val > Decimal("9999999999.999999"):
            raise LexerError(
                f"Float literal `{lexeme}` exceeds maximum value 9999999999.999999 at {line}:{col}",
                self._partial_tokens,
            )
        literal_clean = f"{norm_int}.{truncated_frac}"
        return Token(token_kind, lexeme, literal=literal_clean, line=line, column=col)

    def _string_token(self, quote: str, line: int, col: int) -> Token:
        if quote != '"':
            raise LexerError(
                f'String values must be enclosed in double quotes (") at {line}:{col}',
                self._partial_tokens,
            )
        escaped = False
        content_chars: list[str] = []
        while not self._is_at_end():
            c = self._advance()
            if escaped:
                if c == '"':
                    content_chars.append('"')
                elif c == "\\":
                    content_chars.append("\\")
                elif c == "n":
                    content_chars.append("\n")
                elif c == "t":
                    content_chars.append("\t")
                else:
                    raise LexerError(
                        f"Invalid escape sequence `\\{c}` in string at {line}:{col}",
                        self._partial_tokens,
                    )
                escaped = False
                continue
            if c == "\\":
                escaped = True
                continue
            if c == quote:
                lexeme = self.source[self.start:self.pos]
                inner = "".join(content_chars)
                return Token("STRING_LITERAL", lexeme, literal=inner, line=line, column=col)
            if c == "\n":
                raise LexerError(f"Unterminated string at {line}:{col}", self._partial_tokens)
            content_chars.append(c)
        raise LexerError(f"Unterminated string at {line}:{col}", self._partial_tokens)

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
        raise LexerError("Unterminated block comment", self._partial_tokens)

    def _is_identifier_start(self, ch: str) -> bool:
        # Must start with a letter (no leading underscores per language rules).
        return ch in ALPHA

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

    def _peek_non_whitespace(self) -> str:
        i = self.pos
        while i < self.length and self.source[i] in {" ", "\t", "\r", "\n"}:
            i += 1
        if i >= self.length:
            return "\0"
        return self.source[i]

    def _match(self, expected: str) -> bool:
        if self._is_at_end() or self.source[self.pos] != expected:
            return False
        self.pos += 1
        self.column += 1
        return True

    def _is_at_end(self) -> bool:
        return self.pos >= self.length

    def _format_expected(self, allowed: set[str]) -> str:
        parts: List[str] = []
        if ALNUM.issubset(allowed):
            parts.append("alphanum")
        if " " in allowed or "\t" in allowed:
            parts.append("whitespace")
        for ch in ["(", ")", "[", "]", "{", "}", ";", ",", ":"]:
            if ch in allowed:
                parts.append(repr(ch))
        for ch in ["+", "-", "*", "/", "%", "=", "!", ">", "<", "&", "|", "."]:
            if ch in allowed:
                parts.append(repr(ch))
        if not parts:
            parts.append(", ".join(sorted(repr(a) for a in allowed)))
        return "- " + "- ".join(parts)

    def _validate_symbol_follow(self, lexeme: str, line: int, col: int) -> None:
        if lexeme == "=":
            return
        if lexeme == ";":
            return
        if lexeme in {">", "<", ">=", "<=", "==", "!=", ">>", "<<", "&&", "||"}:
            return
        if lexeme in {"(", ")", "[", "]", "{", "}"}:
            return
        allowed = expanded_reserved_symbol_follows.get(lexeme)
        if not allowed:
            return
        nxt = self._peek_non_whitespace()
        if nxt == "\0":
            return
        if nxt not in allowed:
            expected = self._format_expected(allowed)
            raise LexerError(
                f"Invalid delimiter `{nxt}` after operator `{lexeme}` at {line}:{col}\n\nExpected one of: {expected}",
                self._partial_tokens,
            )

def tokenize(source: str) -> List[Token]:
    return Lexer(source).scan_tokens()

def tokenize_with_errors(source: str) -> (List[Token], List[str]):
    return Lexer(source).scan_tokens_collect_errors()

def _format_tokenizer(tok: Token) -> str:
    display_name_overrides = {
        "(": "parenthesis",
        ")": "parenthesis",
        "{": "brace",
        "}": "brace",
        "[": "bracket",
        "]": "bracket",
        ";": "semicolon",
        ",": "comma",
    }
    # Display lexeme for all tokens (literals use their inner value).
    if tok.literal is not None:
        return tok.literal
    return display_name_overrides.get(tok.lexeme, tok.lexeme)


def _token_type(kind: str) -> str:
    if kind in {"INT_LITERAL"}:
        name = "INT_LIT"
    elif kind in {"FLOAT_LITERAL"}:
        name = "FLOAT_LIT"
    elif kind in {"STRING_LITERAL"}:
        name = "STRING_LIT"
    elif kind in {"CHAR_LITERAL"}:
        name = "CHAR_LIT"
    elif kind in {"BOOL_LITERAL_FALSE", "BOOL_LITERAL_TRUE"}:
        name = "BOOL_LIT"
    else:
        name = TOKEN_TYPE_OVERRIDES.get(kind, kind)
    return name[:12]


def tokens_as_rows(tokens: Iterable[Token]) -> List[dict]:
    rows: List[dict] = []
    for tok in tokens:
        if tok.kind in {"EOF", "NEWLINE"}:
            continue
        rows.append(
            {
                "lexeme": tok.lexeme,
                "token": _format_tokenizer(tok),
                "tokenType": _token_type(tok.kind),
            }
        )
    return rows
