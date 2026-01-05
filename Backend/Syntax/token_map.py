"""Token follow-set mappings for the Lovers language."""

from string import ascii_letters, digits, printable
from typing import Iterable, Set

# --- base character classes -------------------------------------------------

alphabet: Set[str] = set(ascii_letters)
digit: Set[str] = set(digits)
alphanum: Set[str] = alphabet | digit
# string.printable includes whitespace like "\t" and "\n"; exclude those here.
ascii_printable: Set[str] = set(printable) - {"\t", "\n"}


# --- named delimiter/follower sets (as declared in the spec) ----------------

def chars(items: Iterable[str]) -> Set[str]:
    out: Set[str] = set()
    for it in items:
        if isinstance(it, str):
            out.add(it)
    return out


set_defs = {
    "alphabet": {"a : z", "A : Z"},
    "digit" : {"0,1,2,3,4,5,6,7,8,9"},
    "alphanum": {"alphabet", "digit"},
    "arith_op": {"+", "-", "*", "/", "%", "<", ">"},
    "space_del": {" ", "\t", "\n"},
    "give_del": {"space_del",">"},
    "express_del": {"space_del", "<"},
    "overshare_del": {"space_del", "("},
    "condl_del": {"overshare_del"},
    "more_del": {"space_del", "{"},
    "phase_del": {"space_del", "digit", " ' "},
    "love_del": {"space_del", "("},
    "colon_del": {":"},
    "terminator_del": {";"},
    "crement_del": {"alphabet", ";"},
    "flag_del": {";", ":"},
    "comeback_del": {"space_del", ";"},
    "symbol_del": {"space_del", "alphanum"},
    "equal_del": {"space_del", '"'},
    "log_del": {"space_del", "alphanum"},
    "not_del": {"space_del", "alphabet", "("},
    "rel_del": {"space_del", "alphanum"},
    "open_paren_del": {"rel_del", "!"},
    "close_paren_del": {"space_del", "{", "arith_op", "&", "|"},
    "open_brack_del": {"log_del"},
    "close_brack_del": {"space_del", "=", "<", ">"},
    "start_quote_del": {"space_del", "alphanum", "ascii"},
    "end_quote_del": {"space_del", ";", "<"},
    "express_end_del": {"rel_del", '"'},
    "give_end_del": {"space_del", "alphabet"},
    "iden_del" : {"space_del", "arith_op", "=", "&", "|", "["},
    "num_del" : {"space_del", "arith_op", "&", "|", "=", "]", "(", ")", ";"},

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
    "for": {"overshare_del"},
    "forever": {"overshare_del"},
    "more": {"space_del", "{"},
    "forevermore": {"overshare_del"},
    "choose": {"overshare_del"},
    "phase": {"space_del", "digit", "'"},
    "bareminimum": {":"},
    "while": {"overshare_del"},
    "pursue": {"overshare_del"},
    "moveon": {";"},
    "breakup": {";"},
    # Others
    "love": {"space_del", "("},
    "periodt": {";"},
    "const": {"space_del"},
    "greenflag": {";", ":"},
    "redflag": {";", ":"},
    "boundaries": {"space_del"},
    "comeback": {"space_del", ";"},
    "avoidant": {"give_end_del"},
}


# --- Reserved symbols and their expected followers -------------------------

reserved_symbol_follows = {
    # Arithmetic
    "+": {"symbol_del"},
    "-": {"symbol_del"},
    "*": {"symbol_del"},
    "/": {"symbol_del"},
    "%": {"symbol_del"},
    # Assignment
    "=": {"symbol_del", '"', "alphanum", "("},
    "+=": {"symbol_del"},
    "-=": {"symbol_del"},
    "*=": {"symbol_del"},
    "/=": {"symbol_del"},
    "%=": {"symbol_del"},
    # Logical
    "&&": {"symbol_del"},
    "||": {"symbol_del"},
    "!": {"symbol_del"},
    # Relational
    "==": {"symbol_del"},
    "!=": {"symbol_del"},
    ">": {"symbol_del"},
    "<": {"symbol_del"},
    ">=": {"symbol_del"},
    "<=": {"symbol_del"},
    # Unary
    "++": {"alphabet", ";"},
    "--": {"alphabet", ";"},
    # Other
    "(": {"symbol_del", "!"},
    ")": {"space_del", "{", "arith_op", "&", "|"},
    "[": {"log_del"},
    "]": {"space_del", "=", "<", ">"},
    "{": {"space_del"},
    "}": {"space_del, alphabet"},
    ";": {"space_del"},
    ":": {"space_del"},
    "::":{"alphabet"},
    '"': { "ascii"},
    '"': {"space_del", ";",")", "<"},
    "<<": {"symbol_del", '"'},
    ">>": {"space_del", "alphabet"},
    "/*": {"ascii"},
    "*/": {"space_del"},
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
