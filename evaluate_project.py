
import csv
import json
import hmac
import hashlib
import time
import statistics
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PROJECT = Path(r"C:\Users\sarag\SRE_Project")
DATA = PROJECT / "data"
CSV_FILE = DATA / "processed" / "emails.csv"
INDEX_DIR = DATA / "secure_index"
ENC_DIR = DATA / "encrypted_emails"

INDEX_FILE = INDEX_DIR / "keyword_index.json"
INDEX_KEY_FILE = INDEX_DIR / "index_key.bin"
DOC_KEY_FILE = ENC_DIR / "document_key.bin"
MANIFEST_FILE = ENC_DIR / "manifest.json"


def tokenize(text):
    import re
    stop_words = {
        "the", "a", "an", "and", "or", "but", "is", "are",
        "was", "were", "be", "been", "to", "of", "in", "on",
        "for", "with", "at", "by", "from", "as", "it", "this",
        "that", "we", "you", "your", "i", "he", "she", "they",
        "have", "has", "had", "not", "do", "does", "did"
    }
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {
        word for word in words
        if len(word) > 1 and word not in stop_words
    }


def token_for(word, key):
    return hmac.new(
        key, word.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def main():
    with CSV_FILE.open(encoding="utf-8-sig", newline="") as f:
        documents = list(csv.DictReader(f))

    index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    index_key = INDEX_KEY_FILE.read_bytes()
    document_key = DOC_KEY_FILE.read_bytes()
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    aes = AESGCM(document_key)

    # Build an independent plaintext reference for correctness checks.
    reference = {}
    for row in documents:
        doc_id = row["source_file"]
        text = f"{row.get('subject', '')} {row.get('body', '')}"
        for word in tokenize(text):
            reference.setdefault(word, set()).add(doc_id)

    test_words = ["telecom", "enron", "meeting", "energy", "nonexistentword"]
    correct = 0
    search_times = []

    print("SEARCH CORRECTNESS")
    print("-" * 55)

    for word in test_words:
        expected = reference.get(word, set())

        start = time.perf_counter()
        token = token_for(word, index_key)
        actual = set(index.get(token, []))
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Verify that every result can be decrypted and authenticated.
        decrypted_ok = True
        for doc_id in actual:
            try:
                item = manifest[doc_id]
                nonce = __import__("base64").b64decode(item["nonce"])
                ciphertext = (ENC_DIR / item["encrypted_file"]).read_bytes()
                aes.decrypt(nonce, ciphertext, None)
            except Exception:
                decrypted_ok = False
                break

        is_correct = actual == expected and decrypted_ok
        correct += int(is_correct)
        search_times.append(elapsed_ms)

        print(
            f"{word}: expected={len(expected)}, "
            f"found={len(actual)}, correct={is_correct}, "
            f"lookup_ms={elapsed_ms:.4f}, "
            f"decrypt_ok={decrypted_ok}"
        )

    # Measure total encryption payload and original sample sizes.
    original_bytes = sum(
        p.stat().st_size for p in (DATA / "sample").glob("email_*.txt")
    )
    encrypted_bytes = sum(
        (ENC_DIR / item["encrypted_file"]).stat().st_size
        for item in manifest.values()
    )

    overhead = (
        (encrypted_bytes - original_bytes) / original_bytes * 100
        if original_bytes else 0
    )

    print("\nPERFORMANCE SUMMARY")
    print("-" * 55)
    print("Documents:", len(documents))
    print("Test queries:", len(test_words))
    print(f"Correct queries: {correct}/{len(test_words)}")
    print(f"Mean HMAC + index lookup: {statistics.mean(search_times):.4f} ms")
    print(f"Original sample size: {original_bytes:,} bytes")
    print(f"Encrypted payload size: {encrypted_bytes:,} bytes")
    print(f"Ciphertext size overhead: {overhead:.2f}%")
    print("\nNote: lookup time excludes file I/O and decryption.")


if __name__ == "__main__":
    main()
