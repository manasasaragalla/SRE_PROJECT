
import csv
import json
from pathlib import Path

PROJECT = Path(r"C:\Users\sarag\SRE_Project")
DATA = PROJECT / "data"

def size_of(path):
    return path.stat().st_size if path.is_file() else 0

def main():
    print("=" * 60)
    print("SEARCHABLE ENCRYPTION - SECURITY AUDIT")
    print("=" * 60)

    checks = []

    # Plaintext sample emails
    sample_dir = DATA / "sample"
    sample_files = list(sample_dir.glob("email_*.txt"))
    checks.append((
        "Plaintext sample emails",
        len(sample_files),
        sum(size_of(p) for p in sample_files),
        "Plaintext email contents remain on disk."
    ))

    # Plaintext parsed CSV
    csv_path = DATA / "processed" / "emails.csv"
    csv_exists = csv_path.is_file()
    csv_bytes = size_of(csv_path) if csv_exists else 0

    checks.append((
        "Plaintext parsed CSV",
        int(csv_exists),
        csv_bytes,
        "Contains email fields and message bodies."
    ))

    # Original Enron dataset
    raw_dir = DATA / "raw" / "maildir"
    checks.append((
        "Original Enron dataset",
        int(raw_dir.is_dir()),
        0,
        "Original extracted email files remain available."
    ))

    # Encrypted prototype
    encrypted_dir = DATA / "encrypted_emails"
    encrypted_files = list(encrypted_dir.glob("*.enc"))
    checks.append((
        "Encrypted email files",
        len(encrypted_files),
        sum(size_of(p) for p in encrypted_files),
        "Ciphertext is stored separately."
    ))

    # Key files
    key_paths = [
        DATA / "secure_index" / "index_key.bin",
        encrypted_dir / "document_key.bin",
        DATA / "scalability" / "index_key.bin",
        DATA / "scalability" / "document_key.bin",
    ]

    print("\nFILE INVENTORY")
    print("-" * 60)

    for label, count, byte_count, note in checks:
        print(f"{label}: count={count}, bytes={byte_count}")
        print("  Note:", note)

    print("\nKEY FILE CHECK")
    print("-" * 60)

    for key_path in key_paths:
        if key_path.is_file():
            print(f"FOUND: {key_path} ({size_of(key_path)} bytes)")
        else:
            print(f"NOT FOUND: {key_path}")

    # Basic structural checks for the encrypted prototype.
    manifest_path = encrypted_dir / "manifest.json"
    index_path = DATA / "secure_index" / "keyword_index.json"

    print("\nSTRUCTURAL CHECKS")
    print("-" * 60)

    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        print("Manifest entries:", len(manifest))
    else:
        print("Prototype manifest: missing")

    if index_path.is_file():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        print("Keyword tokens:", len(index))
    else:
        print("Prototype keyword index: missing")

    print("\nAUDIT SUMMARY")
    print("-" * 60)
    print("This script only inspects files; it does not delete or modify them.")
    print("Plaintext files and local keys require protection.")
    print("A successful inventory does not prove the system is secure.")

if __name__ == "__main__":
    main()
