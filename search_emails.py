
import csv
import json
import hmac
import hashlib
from pathlib import Path

PROJECT = Path(r"C:\Users\sarag\SRE_Project")
DATA_FILE = PROJECT / "data" / "processed" / "emails.csv"
INDEX_DIR = PROJECT / "data" / "secure_index"
KEY_FILE = INDEX_DIR / "index_key.bin"
INDEX_FILE = INDEX_DIR / "keyword_index.json"


def make_token(keyword, key):
    return hmac.new(
        key,
        keyword.strip().lower().encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def main():
    for path in (DATA_FILE, KEY_FILE, INDEX_FILE):
        if not path.is_file():
            print("ERROR: Required file not found:", path)
            return

    key = KEY_FILE.read_bytes()

    with INDEX_FILE.open("r", encoding="utf-8") as f:
        index = json.load(f)

    documents = {}
    with DATA_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            documents[row["source_file"]] = row

    print("Search is ready. Type 'exit' to quit.")

    while True:
        keyword = input("\nEnter a keyword: ").strip()

        if keyword.lower() == "exit":
            break

        if not keyword or len(keyword.split()) != 1:
            print("Enter one keyword at a time.")
            continue

        token = make_token(keyword, key)
        matches = index.get(token, [])

        if not matches:
            print("No matching emails found.")
            continue

        print(f"\nMatching emails: {len(matches)}")

        for doc_id in matches:
            row = documents.get(doc_id)

            if row:
                print("-" * 50)
                print("File:", doc_id)
                print("Subject:", row.get("subject", "(no subject)"))
                print("Sender:", row.get("sender", "(unknown)"))


if __name__ == "__main__":
    main()
