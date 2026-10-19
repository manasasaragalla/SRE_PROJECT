
import csv
import re
import json
import hmac
import hashlib
import secrets
from pathlib import Path

PROJECT = Path(r"C:\Users\sarag\SRE_Project")
CSV_FILE = PROJECT / "data" / "processed" / "emails.csv"
INDEX_DIR = PROJECT / "data" / "secure_index"

KEY_FILE = INDEX_DIR / "index_key.bin"
INDEX_FILE = INDEX_DIR / "keyword_index.json"

# Common words that usually aren't useful for searching.
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are",
    "was", "were", "be", "been", "to", "of", "in", "on",
    "for", "with", "at", "by", "from", "as", "it", "this",
    "that", "we", "you", "your", "i", "he", "she", "they",
    "have", "has", "had", "not", "do", "does", "did"
}


def tokenize(text):
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {
        word for word in words
        if len(word) > 1 and word not in STOP_WORDS
    }


def make_token(keyword, key):
    return hmac.new(
        key,
        keyword.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def main():
    if not CSV_FILE.is_file():
        print("ERROR: emails.csv not found. Run parse_emails.py first.")
        return

    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    # Keep the same secret key across runs.
    if KEY_FILE.exists():
        key = KEY_FILE.read_bytes()
    else:
        key = secrets.token_bytes(32)
        KEY_FILE.write_bytes(key)

    index = {}
    document_count = 0

    with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            doc_id = row["source_file"]
            text = f"{row.get('subject', '')} {row.get('body', '')}"

            for keyword in tokenize(text):
                token = make_token(keyword, key)
                index.setdefault(token, []).append(doc_id)

            document_count += 1

    # Remove duplicate document IDs and keep output deterministic.
    index = {
        token: sorted(set(doc_ids))
        for token, doc_ids in index.items()
    }

    with INDEX_FILE.open("w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    print("Documents indexed:", document_count)
    print("Unique keyword tokens:", len(index))
    print("Index saved to:", INDEX_FILE)
    print("Secret key saved locally:", KEY_FILE)
    print("Keep the key private; do not upload it publicly.")


if __name__ == "__main__":
    main()
