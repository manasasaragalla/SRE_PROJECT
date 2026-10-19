
import base64
import hashlib
import hmac
import json
from email import policy
from email.parser import BytesParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

BASE_DIR = Path(__file__).resolve().parent
INDEX_KEY_FILE = BASE_DIR / "data" / "secure_index" / "index_key.bin"
DOCUMENT_KEY_FILE = BASE_DIR / "data" / "encrypted_emails" / "document_key.bin"
SERVER_URL = "http://127.0.0.1:5000"


def make_token(keyword, key):
    return hmac.new(
        key, keyword.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def search_server(token):
    payload = json.dumps({"token": token}).encode("utf-8")
    req = Request(
        f"{SERVER_URL}/search",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_matches(keywords, index_key):
    """Return a mapping from document ID to its encrypted result."""
    matches = {}

    for keyword in keywords:
        token = make_token(keyword, index_key)
        print(f"[CLIENT] Searching for '{keyword}', token={token[:16]}...")

        response = search_server(token)

        for item in response.get("results", []):
            matches.setdefault(item["doc_id"], item)

    return matches


def main():
    if not INDEX_KEY_FILE.is_file() or not DOCUMENT_KEY_FILE.is_file():
        print("[CLIENT] Required key file not found.")
        return

    index_key = INDEX_KEY_FILE.read_bytes()
    document_key = DOCUMENT_KEY_FILE.read_bytes()
    aesgcm = AESGCM(document_key)

    print("=== Secure Search Email Client ===")
    print("Enter multiple words separated by spaces.")
    print("Type 'exit' to quit.")

    while True:
        query = input("\n[USER] Search keywords: ").strip().lower()

        if query == "exit":
            print("[CLIENT] Exiting.")
            break

        keywords = query.split()

        if not keywords:
            print("[CLIENT] Enter at least one keyword.")
            continue

        if any(not keyword.isalnum() for keyword in keywords):
            print("[CLIENT] Use letters or numbers separated by spaces.")
            continue

        mode = input("[USER] Search mode (OR/AND): ").strip().upper()
        if mode not in ("OR", "AND"):
            print("[CLIENT] Enter OR or AND.")
            continue

        try:
            per_keyword = []
            for keyword in keywords:
                token = make_token(keyword, index_key)
                print(f"[CLIENT] Generated token for '{keyword}': {token[:16]}...")
                response = search_server(token)
                per_keyword.append({
                    item["doc_id"]: item
                    for item in response.get("results", [])
                })

            if mode == "OR":
                results = {}
                for result_set in per_keyword:
                    results.update(result_set)
            else:
                common_ids = set(per_keyword[0])
                for result_set in per_keyword[1:]:
                    common_ids.intersection_update(result_set)
                results = {
                    doc_id: per_keyword[0][doc_id]
                    for doc_id in common_ids
                }

            print(f"[CLIENT] {mode} search returned {len(results)} email(s).")

            if not results:
                print("[CLIENT] No matching emails found.")
                continue

            for item in results.values():
                try:
                    nonce = base64.b64decode(item["nonce"], validate=True)
                    ciphertext = base64.b64decode(item["ciphertext"], validate=True)
                    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
                    message = BytesParser(policy=policy.default).parsebytes(plaintext)

                    print("-" * 55)
                    print("[CLIENT] Decryption successful")
                    print("Document:", item["doc_id"])
                    print("Subject:", message.get("Subject", "(unknown)"))
                    print("Sender:", message.get("From", "(unknown)"))
                    print("Date:", message.get("Date", "(unknown)"))
                except Exception:
                    print(f"[CLIENT] Could not decrypt {item['doc_id']}.")

        except HTTPError as exc:
            print(f"[CLIENT] Server returned HTTP {exc.code}.")
        except URLError:
            print("[CLIENT] Cannot connect. Is server.py running?")
        except TimeoutError:
            print("[CLIENT] Server request timed out.")


if __name__ == "__main__":
    main()
