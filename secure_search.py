
import json
import hmac
import hashlib
import base64
from pathlib import Path
from email import policy
from email.parser import BytesParser
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PROJECT = Path(r"C:\Users\sarag\SRE_Project")
INDEX_DIR = PROJECT / "data" / "secure_index"
ENCRYPTED_DIR = PROJECT / "data" / "encrypted_emails"

INDEX_FILE = INDEX_DIR / "keyword_index.json"
INDEX_KEY_FILE = INDEX_DIR / "index_key.bin"
DOC_KEY_FILE = ENCRYPTED_DIR / "document_key.bin"
MANIFEST_FILE = ENCRYPTED_DIR / "manifest.json"


def make_token(keyword, key):
    return hmac.new(
        key,
        keyword.strip().lower().encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def decrypt_email(doc_id, aesgcm, manifest):
    entry = manifest.get(doc_id)
    if not entry:
        raise ValueError(f"No manifest entry for {doc_id}")

    encrypted_path = ENCRYPTED_DIR / entry["encrypted_file"]
    nonce = base64.b64decode(entry["nonce"])
    ciphertext = encrypted_path.read_bytes()

    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return BytesParser(policy=policy.default).parsebytes(plaintext)


def main():
    required = [
        INDEX_FILE,
        INDEX_KEY_FILE,
        DOC_KEY_FILE,
        MANIFEST_FILE,
    ]

    for path in required:
        if not path.is_file():
            print("ERROR: Missing required file:", path)
            return

    index_key = INDEX_KEY_FILE.read_bytes()
    document_key = DOC_KEY_FILE.read_bytes()

    index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    aesgcm = AESGCM(document_key)

    print("Encrypted search ready. Type 'exit' to quit.")

    while True:
        keyword = input("\nEnter a keyword: ").strip()

        if keyword.lower() == "exit":
            break

        if not keyword or len(keyword.split()) != 1:
            print("Enter one keyword at a time.")
            continue

        token = make_token(keyword, index_key)
        matches = index.get(token, [])

        if not matches:
            print("No matching emails found.")
            continue

        print("Matching encrypted emails:", len(matches))

        for doc_id in matches:
            try:
                message = decrypt_email(doc_id, aesgcm, manifest)
                print("-" * 50)
                print("File:", doc_id)
                print("Subject:", message.get("Subject", "(no subject)"))
                print("Sender:", message.get("From", "(unknown)"))
            except Exception as error:
                print("Could not decrypt", doc_id, "-", error)


if __name__ == "__main__":
    main()
