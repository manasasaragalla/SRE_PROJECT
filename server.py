# server.py
import base64
import json
import re
from pathlib import Path

from flask import Flask, jsonify, request

BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "data" / "secure_index" / "keyword_index.json"
ENCRYPTED_DIR = BASE_DIR / "data" / "encrypted_emails"
MANIFEST_FILE = ENCRYPTED_DIR / "manifest.json"

app = Flask(__name__)


def load_server_data():
    """Load only the searchable index and encrypted-file metadata."""
    for path in (INDEX_FILE, MANIFEST_FILE):
        if not path.is_file():
            raise FileNotFoundError(f"Required file not found: {path}")

    index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    return index, manifest


@app.get("/health")
def health():
    return jsonify({"status": "running", "service": "search-server"})


@app.post("/search")
def search():
    payload = request.get_json(silent=True) or {}
    token = payload.get("token", "")

    # Accept a SHA-256 HMAC digest in hexadecimal form.
    if not isinstance(token, str) or not re.fullmatch(r"[0-9a-f]{64}", token):
        return jsonify({"error": "Invalid search token"}), 400

    try:
        index, manifest = load_server_data()
        document_ids = index.get(token, [])

        results = []
        for doc_id in document_ids:
            entry = manifest.get(doc_id)
            if not entry:
                continue

            filename = entry.get("encrypted_file", "")
            encrypted_path = (ENCRYPTED_DIR / filename).resolve()

            # Ensure a manifest entry cannot make the server read outside
            # the encrypted-email directory.
            if encrypted_path.parent != ENCRYPTED_DIR.resolve():
                continue

            if not encrypted_path.is_file():
                continue

            results.append({
                "doc_id": doc_id,
                "nonce": entry["nonce"],
                "ciphertext": base64.b64encode(
                    encrypted_path.read_bytes()
                ).decode("ascii"),
            })

        # For the demo, log only a short token prefix, not email contents.
        print(
            f"[SERVER] Search request received. "
            f"Token prefix={token[:12]}..., matches={len(results)}"
        )

        return jsonify({
            "count": len(results),
            "results": results,
        })

    except (OSError, ValueError, KeyError, TypeError) as exc:
        app.logger.exception("Search failed")
        return jsonify({"error": "Search failed", "detail": str(exc)}), 500


if __name__ == "__main__":
    print("[SERVER] Starting searchable-email server on 127.0.0.1:5000")
    # Local demonstration only; do not expose this development server publicly.
    app.run(host="127.0.0.1", port=5000, debug=False)