from flask import Flask, jsonify, request
from flask_cors import CORS

from Backend.Lexical import Lexer, tokens_as_rows, tokenize_with_errors
from Backend.Lexical.Lexer import LexerError
from Backend.Syntax.syntax_analyzer import analyze as syntax_analyze

app = Flask(__name__)
CORS(app, resources={r"/lex": {"origins": "*"}, r"/validate": {"origins": "*"}})

@app.post("/lex")
def lex():
    payload = request.get_json(silent=True) or {}
    source = payload.get("source", "")
    if not isinstance(source, str):
        return jsonify({"error": "`source` must be a string"}), 400

    try:
        tokens, errors = tokenize_with_errors(source)
        payload = {"rows": tokens_as_rows(tokens)}
        if errors:
            payload["error"] = errors[0]
            payload["errors"] = errors
        return jsonify(payload), 200
    except LexerError as exc:
        # Return partial tokens with the error so UI can show stream + terminal error.
        rows = tokens_as_rows(getattr(exc, "tokens", []) or [])
        return jsonify({"rows": rows, "error": f"Lexing failed: {exc}"}), 200
    except Exception as exc:
        return jsonify({"error": f"Lexing failed: {exc}"}), 400

    return jsonify({"rows": tokens_as_rows(tokens)})


@app.post("/validate")
def validate():
    payload = request.get_json(silent=True) or {}
    source = payload.get("source", "")
    if not isinstance(source, str):
        return jsonify({"error": "`source` must be a string"}), 400

    ok, result = syntax_analyze(source)
    if ok:
        return jsonify({"ok": True, "message": "Syntax OK"}), 200
    return jsonify(result), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # flip debug=False for production   
