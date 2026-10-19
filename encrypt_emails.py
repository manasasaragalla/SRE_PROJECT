
import os
import json
import base64
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PROJECT = Path(r"C:\Users\sarag\SRE_Project")
SAMPLE_DIR = PROJECT / "data" / "sample"
SECURE_DIR = PROJECT / "data" / "encrypted_emails"
KEY_FILE = SECURE_DIR / "document_key.bin"
MANIFEST_FILE = SECURE_DIR / "manifest.json"


def main():
    SECURE_DIR.mkdir(parents=True, exist_ok=True)

    # Create a 256-bit key once and reuse it for decryption.
    if KEY_FILE.exists():
        key = KEY_FILE.read_bytes()
        if len(key) != 32:
            raise ValueError("Document key must be exactly 32 bytes.")
    else:
        key = AESGCM.generate_key(bit_length=256)
        KEY_FILE.write_bytes(key)

    aesgcm = AESGCM(key)
    manifest = {}
    encrypted_count = 0

    files = sorted(SAMPLE_DIR.glob("email_*.txt"))

    if not files:
        print("ERROR: No sample email files found.")
        return

    for file_path in files:
        plaintext = file_path.read_bytes()

        # AES-GCM requires a unique nonce for each encryption
        # under the same key.
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        encrypted_path = SECURE_DIR / f"{file_path.stem}.enc"
        encrypted_path.write_bytes(ciphertext)

        manifest[file_path.name] = {
            "encrypted_file": encrypted_path.name,
            "nonce": base64.b64encode(nonce).decode("ascii"),
        }

        encrypted_count += 1

    MANIFEST_FILE.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8"
    )

    print("Documents encrypted:", encrypted_count)
    print("Encrypted files:", SECURE_DIR)
    print("Manifest:", MANIFEST_FILE)
    print("Key file:", KEY_FILE)
    print("Keep the key and manifest private.")


if __name__ == "__main__":
    main()
