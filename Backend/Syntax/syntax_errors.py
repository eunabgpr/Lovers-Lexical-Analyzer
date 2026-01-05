"""Helpers for building syntax error payloads."""

from __future__ import annotations

from typing import List, Optional


def make_error(
    message: str,
    token: Optional[object],
    expected: Optional[List[str]] = None,
    code: str = "ERR_SYNTAX",
) -> dict:
    expected = expected or []
    lexeme = getattr(token, "lexeme", "") if token else ""
    kind = getattr(token, "kind", "EOF") if token else "EOF"
    line = getattr(token, "line", 0) if token else 0
    column = getattr(token, "column", 0) if token else 0
    return {
        "ok": False,
        "code": code,
        "message": message,
        "expected": expected,
        "token": {
            "lexeme": lexeme,
            "kind": kind,
            "line": line,
            "column": column,
        },
    }
