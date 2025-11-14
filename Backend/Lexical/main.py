from flask import Flask, request, jsonify
from flask_cors import CORS
from Backend.Lexical import Lexer, tokens_as_rows

app = Flask(__name__)
CORS(app, resources={r"/lex": {"origins": "*"}})

@app.post("/lex")
def lex():
    payload = request.get_json(silent=True) or {}
    source = payload.get("source", "")
    if not isinstance(source, str):
        return jsonify({"error": "`source` must be a string"}), 400

    try:
        tokens = Lexer(source).scan_tokens()
    except Exception as exc:
        return jsonify({"error": f"Lexing failed: {exc}"}), 400

    return jsonify({"rows": tokens_as_rows(tokens)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # flip debug=False for production   
