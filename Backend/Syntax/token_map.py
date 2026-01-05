"""Token follow-set mappings for the Lovers language."""

from string import ascii_letters, digits, printable
from typing import Iterable, Set

# --- base character classes -------------------------------------------------

alphabet: Set[str] = set(ascii_letters)
digit: Set[str] = set(digits)
alphanum: Set[str] = alphabet | digit
ascii_printable: Set[str] = set(printable)


# --- named delimiter/follower sets (as declared in the spec) ----------------

def chars(items: Iterable[str]) -> Set[str]:
    out: Set[str] = set()
    for it in items:
        if isinstance(it, str):
            out.add(it)
    return out


set_defs = {
    "space_del": {" ", "\t", "\n"},
    "symbol_del": {">", "<"},  # can be extended if needed
    "arith_op": {"+", "-", "*", "/", "%", "<", ">"},
    "gen_op": {"+", "-", "*", "/", "%", "<", ">", "=", "!", "&", "|"},
    "sim_del": {"/", ";"},
    "same_del": {" ", "\t", "("},
    "iden_del": {" ", "\t", "(", ")", "[", "]"} | {"+", "-", "*", "/", "%", "<", ">", "=", "!", "&", "|"},
    "condl_del": {"/", ";", "("},
    "status_del": {":", ",", ")", "]", "}", "+", "-", "*", "/", "%", "=", "!", "&", "|", ";", "/"},
    "close_brce_del": {",", ")", "}", ";", "/"},
    "close_brck_del": {":", ",", "(", ")", "[", "]", "}", "+", "-", "*", "/", "%", "=", "!", "&", "|", ";", "/"},
    "close_paren_del": {"+", "-", "*", "/", "%", "<", ">", "=", "!", "&", "|", "{", "}", ";", "/"},
    "bareminimum_del": {":"},
    "terminator_del": {"/", ";"},
    "love_del": {"/", ";", "{"},
    "give_del": {"/", ";", ">"},
    "express_del": {"/", ";", "<"},
    "boolean_del": {":", ";", "+", "-", "*", "/", "%", "<", ">", "=", "!", "&", "|", ")", "]", "}", ";", "/"},
    "eql_comma_del": {'"', "+", "-", "!", "(", "{", ";" , "/"},
    "more_del": {"{", "/", ";"},
    "log_not_del": {'"', "-", "!", "(", "/", ";"},
    "minus_del": {'"', "(", "!", "/", ";"},
    "symbols_del": {"-", "(", '"', "!", "/", ";"},
    "open_brce_del": {'"', "-", "!", "(", "{", "}", "/", ";"},
    "open_brck_del": {"-", "(", "]", "/", ";"},
    "open_paren_del": {'"', "+", "-", "!", "(", ")", "{", "/", ";"},
    "add_and_or_del": {'"', "-", "(", "!", "/", ";"},
    "push_del": {"(", "/", ";"},
    "rant_del": {":", ";", ",", "+", "-", "*", "&", "|", "%", "=", "!", ")", "[", "}", "/", ";"},
    "end_del": set(alphabet) | {"/", ";"},
    "unary_del": {";", "+", "-", "*", "/", "%", "<", ">", "=", "!", "&", "|", ")", "/"},
    "dear_dearest_del": {":", ";", "+", "-", "*", "/", "%", "=", "!", "&", "|", ")", "}", "]", "/", ";"},
    "comeback_del": {" ", "\t", "(", "/", ";"} | alphanum,
    "comnt_del": {" ", "\t", "\n"},
}


# --- Reserved words and their expected followers ---------------------------

reserved_word_follows = {
    # Data Types
    "dear": {"space_del"},
    "dearest": {"space_del"},
    "rant": {"space_del"},
    "status": {"space_del"},
    # I/O
    "give": {"space_del", ">"},
    "express": {"space_del", "<"},
    "overshare": {"space_del", "("},
    # Conditionals / Loops
    "for": {"space_del", "("},
    "forever": {"space_del", "("},
    "forevermore": {"space_del", "("},
    "choose": {"space_del", "("},
    "more": {"space_del", "{"},
    "phase": {"space_del", "digit", "'"},
    "bareminimum": {":"},
    "while": {"space_del", "("},
    "pursue": {"space_del", "("},
    "moveon": {";"},
    "breakup": {";"},
    # Others
    "love": {"space_del"},
    "periodt": {";"},
    "const": {"space_del"},
    "greenflag": {";", ":"},
    "redflag": {";", ":"},
    "boundaries": {"space_del"},
    "comeback": {";", "alphanum"},
}


# --- Reserved symbols and their expected followers -------------------------

reserved_symbol_follows = {
    # Arithmetic
    "+": {"space_del", "alphanum", "(", '"', ";"},
    "-": {"space_del", "alphanum", "("},
    "*": {"space_del", "alphanum", "("},
    "/": {"space_del", "alphanum", "("},
    "%": {"space_del", "alphanum", "("},
    # Assignment
    "=": {"space_del", '"', "alphanum", "("},
    "+=": {"space_del", "alphanum", "("},
    "-=": {"space_del", "alphanum", "("},
    "*=": {"space_del", "alphanum", "("},
    "/=": {"space_del", "alphanum", "("},
    "%=": {"space_del", "alphanum", "("},
    # Logical
    "&&": {"space_del", "alphanum"},
    "||": {"space_del", "alphanum"},
    "!": {"space_del", "alphabet", "("},
    # Relational
    "==": {"space_del", "alphanum"},
    "!=": {"space_del", "alphanum"},
    ">": {"symbol_del"},
    "<": {"symbol_del"},
    ">=": {"symbol_del"},
    "<=": {"symbol_del"},
    # Unary
    "++": {"space_del", "alphanum", "("},
    "--": {"space_del", "alphanum", "("},
    # Other
    "(": {"symbol_del", "!"},
    ")": {"space_del", "{", "arith_op", "&", "|"},
    "[": {"space_del", "alphanum"},
    "]": {"space_del", "=", "<", ">"},
    ";": {"space_del", "}","\t"},
    '"': {"space_del", "alphanum", "ascii"},
    "<<": {"space_del", '"', "alphanum", "("},
    ">>": {"space_del", "alphabet"},
    "/*": {"comnt_del"},
    "*/": {"sim_del"},
}


# --- Identifier followers ---------------------------------------------------

identifier_follows = {
    "variant_1": {"space_del", "arith_op", "=", "&", "|", "["},
    "variant_2": {"space_del", "arith_op", "&", "|", "=", "]", "(", ")", ";"},
}


# --- Utility to expand named sets into concrete characters ------------------

def resolve_set(name: str) -> Set[str]:
    if name == "alphabet":
        return set(alphabet)
    if name == "digit":
        return set(digit)
    if name == "alphanum":
        return set(alphanum)
    if name in set_defs:
        return set(set_defs[name])
    if name == "space_del":
        return {" ", "\t", "\n"}
    if name == "ascii":
        return set(ascii_printable)
    return {name}  # fallback: literal char/name


def expand_follow(raw: Iterable[str]) -> Set[str]:
    out: Set[str] = set()
    for item in raw:
        if len(item) == 1:
            out.add(item)
        else:
            out |= resolve_set(item)
    return out


expanded_reserved_word_follows = {
    word: expand_follow(spec) for word, spec in reserved_word_follows.items()
}

expanded_reserved_symbol_follows = {
    sym: expand_follow(spec) for sym, spec in reserved_symbol_follows.items()
}

expanded_identifier_follows = {
    name: expand_follow(spec) for name, spec in identifier_follows.items()
}
