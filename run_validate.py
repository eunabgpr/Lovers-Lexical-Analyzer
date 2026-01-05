import sys
from pathlib import Path

# Ensure project root is on sys.path so `Backend` can be imported when run from anywhere.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Backend.Lexical import Lexer, validate_program_structure
from Backend.Lexical.Lexer import LexerError


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python run_validate.py <source_file>")
        return 1

    src_path = Path(sys.argv[1])
    if not src_path.exists():
        print(f"File not found: {src_path}")
        return 1

    source = src_path.read_text(encoding="utf-8")
    try:
        tokens = Lexer(source).scan_tokens()
        result = validate_program_structure(tokens)
    except LexerError as exc:  # pragma: no cover - defensive user feedback
        print(f"Lexing failed: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - defensive user feedback
        print(f"Validation failed: {exc}")
        return 1

    if result.get("ok"):
        print(result)
        return 0

    # Provide a more helpful, delimiter-focused message when available.
    token = result.get("token")
    expected = result.get("expected")
    if expected:
        expect_msg = f"Expected one of: {', '.join(expected)}"
    else:
        expect_msg = None

    parts = [
        f"Validation error: {result.get('message', 'Unknown error')}",
        f"Code: {result.get('code', 'N/A')}",
    ]
    if token:
        parts.append(
            f"At line {token.get('line', '?')}, column {token.get('column', '?')}: found `{token.get('lexeme', '?')}` ({token.get('kind', '?')})"
        )
    if expect_msg:
        parts.append(expect_msg)

    print("\n".join(parts))
    return 1


if __name__ == "__main__":
    sys.exit(main())
