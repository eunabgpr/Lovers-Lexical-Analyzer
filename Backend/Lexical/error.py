from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from .Lexer import Token

IGNORED_KINDS = {"NEWLINE", "EOF"}
DELIM_OPEN_TO_CLOSE = {"(": ")", "{": "}", "[": "]"}
DELIM_CLOSE_TO_OPEN = {v: k for k, v in DELIM_OPEN_TO_CLOSE.items()}
DELIM_MISSING_CODES = {
    "(": "ERR_EXPECTED_RPAREN",
    "{": "ERR_EXPECTED_RBRACE",
    "[": "ERR_EXPECTED_RBRACKET",
}
DELIM_UNEXPECTED_CODES = {
    ")": "ERR_UNEXPECTED_RPAREN",
    "}": "ERR_UNEXPECTED_RBRACE",
    "]": "ERR_UNEXPECTED_RBRACKET",
}

ALLOWED_TYPE_KINDS = {
    "KEYWORD_TYPE_INT",  # dear
    "KEYWORD_TYPE_FLOAT",  # dearest
    "KEYWORD_TYPE_STRING",  # rant
    "KEYWORD_TYPE_BOOL",  # status
    "IDENTIFIER",  # user-defined types
}


def validate_program_structure(tokens: List[Token]) -> Dict[str, object]:
    """
    Validates the high-level structure of a Lovers program. Ensures sources start
    with `love <identifier>() { ... }`, permits zero or more C++-style global
    declarations before `love`, enforces balanced delimiters, and checks that the
    main block closes the program with nothing after it.
    """
    filtered = [t for t in tokens if t.kind not in IGNORED_KINDS]
    if not filtered:
        return _failure(
            "ERR_EMPTY", "Source is empty. Expected `love <identifier>() { ... }`."
        )

    err = _check_balanced_delimiters(filtered)
    if err:
        return err

    idx = 0
    while idx < len(filtered) and _looks_like_cpp_decl(filtered, idx):
        idx, err = _consume_cpp_decl(filtered, idx)
        if err:
            return err

    if idx >= len(filtered):
        return _success("Structure looks valid (globals only).")

    consumed, err = _consume_main_signature(filtered[idx:])
    if err:
        return err
    idx += consumed

    err = _ensure_program_ends_after_main(filtered, idx)
    if err:
        return err

    return _success("Structure looks valid.")


def _success(message: str) -> Dict[str, object]:
    return {"ok": True, "message": message}


def _failure(
    code: str, message: str, token: Token | None = None, expected: List[str] | None = None
) -> Dict[str, object]:
    payload = {"ok": False, "code": code, "message": message}
    if expected:
        payload["expected"] = expected
    if token:
        payload["token"] = {
            "lexeme": token.lexeme,
            "kind": token.kind,
            "line": token.line,
            "column": token.column,
        }
    return payload


def _consume_main_signature(tokens: Sequence[Token]) -> Tuple[int, Dict[str, object] | None]:
    idx = 0

    def expect(predicate, message: str, code: str, expected: Sequence[str]):
        nonlocal idx
        if idx >= len(tokens) or not predicate(tokens[idx]):
            offending = tokens[idx] if idx < len(tokens) else None
            return False, _failure(code, message, offending, list(expected))
        idx += 1
        return True, None

    checks: List[Tuple] = [
        (
            lambda t: t.lexeme == "love",
            "Program must start with `love` keyword.",
            "ERR_EXPECTED_LOVE",
            ["love"],
        ),
        (
            lambda t: t.kind == "IDENTIFIER",
            "Expected identifier after `love`.",
            "ERR_EXPECTED_MAIN",
            ["<identifier>"],
        ),
        (
            lambda t: t.lexeme == "(",
            "Expected `(` after `main`.",
            "ERR_EXPECTED_LPAREN",
            ["("],
        ),
        (
            lambda t: t.lexeme == ")",
            "Expected `)` to close parameters.",
            "ERR_EXPECTED_RPAREN",
            [")"],
        ),
        (
            lambda t: t.lexeme == "{",
            "Expected `{` to start main block.",
            "ERR_EXPECTED_LBRACE",
            ["{"],
        ),
    ]

    for predicate, message, code, expected in checks:
        ok, failure = expect(predicate, message, code, expected)
        if not ok:
            return idx, failure

    return idx, None


def _check_balanced_delimiters(tokens: Sequence[Token]) -> Dict[str, object] | None:
    stack: List[Token] = []
    for tok in tokens:
        lex = tok.lexeme
        if lex in DELIM_OPEN_TO_CLOSE:
            stack.append(tok)
            continue
        if lex in DELIM_CLOSE_TO_OPEN:
            if not stack:
                return _failure(
                    DELIM_UNEXPECTED_CODES[lex],
                    f"Found closing `{lex}` without a matching `{DELIM_CLOSE_TO_OPEN[lex]}`.",
                    token=tok,
                    expected=[DELIM_CLOSE_TO_OPEN[lex]],
                )
            opening = stack.pop()
            if opening.lexeme != DELIM_CLOSE_TO_OPEN[lex]:
                expected = DELIM_OPEN_TO_CLOSE[opening.lexeme]
                return _failure(
                    DELIM_MISSING_CODES[opening.lexeme],
                    f"Expected `{expected}` to close `{opening.lexeme}` opened at line {opening.line}, column {opening.column}, but found `{lex}`.",
                    token=tok,
                    expected=[expected],
                )

    if stack:
        opening = stack[-1]
        expected = DELIM_OPEN_TO_CLOSE[opening.lexeme]
        return _failure(
            DELIM_MISSING_CODES[opening.lexeme],
            f"Missing closing `{expected}` for `{opening.lexeme}` opened at line {opening.line}, column {opening.column}.",
            token=opening,
            expected=[expected],
        )

    return None


def _ensure_program_ends_after_main(tokens: Sequence[Token], start_idx: int) -> Dict[str, object] | None:
    brace_depth = 1
    for pos in range(start_idx, len(tokens)):
        tok = tokens[pos]
        if tok.lexeme == "{":
            brace_depth += 1
        elif tok.lexeme == "}":
            brace_depth -= 1
            if brace_depth == 0:
                if pos != len(tokens) - 1:
                    next_tok = tokens[pos + 1]
                    return _failure(
                        "ERR_UNEXPECTED_TOKEN_AFTER_MAIN",
                        "Program must end immediately after the closing `}` of the `love` block.",
                        token=next_tok,
                    )
                return None

    return _failure(
        "ERR_EXPECTED_RBRACE",
        "Missing closing `}` for the `love` block.",
        expected=["}"],
    )


def _looks_like_cpp_decl(tokens: Sequence[Token], idx: int) -> bool:
    """
    Heuristic: a global declaration starts with a type token and an identifier name.
    """
    return (
        idx + 1 < len(tokens)
        and tokens[idx].kind in ALLOWED_TYPE_KINDS
        and tokens[idx + 1].kind == "IDENTIFIER"
    )


def _consume_cpp_decl(tokens: Sequence[Token], idx: int) -> Tuple[int, Dict[str, object] | None]:
    """
    Consumes a C++-style global declaration or function definition/prototype.
    Returns the next index after the declaration and an optional error.
    """
    i = idx + 2  # skip type + name

    # Function: type name ( ... ) { ... }  OR prototype: type name ( ... );
    if i < len(tokens) and tokens[i].lexeme == "(":
        paren_depth = 1
        j = i + 1
        while j < len(tokens) and paren_depth > 0:
            if tokens[j].lexeme == "(":
                paren_depth += 1
            elif tokens[j].lexeme == ")":
                paren_depth -= 1
            j += 1

        if paren_depth != 0:
            offending = tokens[j - 1] if j - 1 < len(tokens) else None
            return idx, _failure(
                "ERR_EXPECTED_RPAREN",
                "Unterminated parameter list in global declaration.",
                token=offending,
                expected=[")"],
            )

        after_paren = j
        if after_paren < len(tokens) and tokens[after_paren].lexeme == ";":
            return after_paren + 1, None  # prototype ends here

        if after_paren < len(tokens) and tokens[after_paren].lexeme == "{":
            brace_depth = 1
            k = after_paren + 1
            while k < len(tokens) and brace_depth > 0:
                if tokens[k].lexeme == "{":
                    brace_depth += 1
                elif tokens[k].lexeme == "}":
                    brace_depth -= 1
                k += 1
            if brace_depth != 0:
                offending = tokens[k - 1] if k - 1 < len(tokens) else None
                return idx, _failure(
                    "ERR_EXPECTED_RBRACE",
                    "Unterminated global function body.",
                    token=offending,
                    expected=["}"],
                )
            return k, None

        offending = tokens[after_paren] if after_paren < len(tokens) else None
        return idx, _failure(
            "ERR_EXPECTED_LBRACE_OR_SEMICOLON",
            "Expected `{` for function body or `;` for prototype.",
            token=offending,
            expected=["{", ";"],
        )

    # Variable declaration: type name [= ...] ;
    while i < len(tokens) and tokens[i].lexeme != ";":
        i += 1

    if i >= len(tokens):
        return idx, _failure(
            "ERR_EXPECTED_SEMICOLON",
            "Missing `;` after global declaration.",
            expected=[";"],
        )

    return i + 1, None
