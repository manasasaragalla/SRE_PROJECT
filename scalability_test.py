
import os
import re
import csv
import json
import time
import hmac
import hashlib
import statistics
from pathlib import Path
from email import policy
from email.parser import BytesParser

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


PROJECT = Path(r"C:\Users\sarag\SRE_Project")
RAW = str(PROJECT / "data" / "raw" / "maildir")
OUT = PROJECT / "data" / "scalability"
ENC_DIR = OUT / "encrypted"
RESULTS = OUT / "scalability_results.csv"

SIZES = [100, 1000, 5000]
QUERIES = ["telecom", "enron", "meeting", "energy"]

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


def make_token(word, key):
    return hmac.new(
        key, word.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def parse_message(raw_bytes):
    msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)

    subject = str(msg.get("Subject", ""))
    body_part = msg.get_body(preferencelist=("plain",))
    body = ""

    if body_part:
        try:
            body = body_part.get_content()
        except (ValueError, TypeError):
            body = ""

    if not body and not msg.is_multipart():
        try:
            body = msg.get_content()
        except (ValueError, TypeError):
            pass

    return subject, body


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ENC_DIR.mkdir(parents=True, exist_ok=True)

    if not os.path.isdir(RAW):
        print("ERROR: Enron maildir folder not found:", RAW)
        return

    # Separate keys for this experiment.
    hmac_key_file = OUT / "index_key.bin"
    aes_key_file = OUT / "document_key.bin"

    if hmac_key_file.exists():
        hmac_key = hmac_key_file.read_bytes()
    else:
        hmac_key = os.urandom(32)
        hmac_key_file.write_bytes(hmac_key)

    if aes_key_file.exists():
        aes_key = aes_key_file.read_bytes()
        if len(aes_key) != 32:
            raise ValueError("Invalid AES key length.")
    else:
        aes_key = AESGCM.generate_key(bit_length=256)
        aes_key_file.write_bytes(aes_key)

    aes = AESGCM(aes_key)

    # Extended paths are needed for Enron filenames ending in dots.
    raw_extended = "\\\\?\\" + RAW

    index = {}
    reference = {}
    manifest = {}
    results = []
    original_bytes = 0
    encrypted_bytes = 0
    parsed_count = 0
    failed_count = 0

    index_seconds = 0.0
    encryption_seconds = 0.0
    checkpoints = set(SIZES)

    print("Starting scalability experiment...")
    print("Target sizes:", SIZES)

    for person in os.scandir(raw_extended):
        if not person.is_dir():
            continue

        email_folder = os.path.join(person.path, "all_documents")
        if not os.path.isdir(email_folder):
            continue

        try:
            entries = os.scandir(email_folder)
        except OSError:
            continue

        with entries:
            for entry in entries:
                if not entry.is_file():
                    continue

                if parsed_count >= max(SIZES):
                    break

                try:
                    with open(entry.path, "rb") as f:
                        raw_bytes = f.read()

                    subject, body = parse_message(raw_bytes)
                    doc_id = f"doc_{parsed_count + 1:05d}"
                    words = tokenize(subject + " " + body)

                    # Time keyword-index construction.
                    start = time.perf_counter()
                    for word in words:
                        reference.setdefault(word, set()).add(doc_id)
                        token = make_token(word, hmac_key)
                        index.setdefault(token, []).append(doc_id)
                    index_seconds += time.perf_counter() - start

                    # Time encryption and writing ciphertext.
                    nonce = os.urandom(12)
                    start = time.perf_counter()
                    ciphertext = aes.encrypt(nonce, raw_bytes, None)
                    encrypted_path = ENC_DIR / f"{doc_id}.enc"
                    encrypted_path.write_bytes(ciphertext)
                    encryption_seconds += time.perf_counter() - start

                    manifest[doc_id] = {
                        "file": encrypted_path.name,
                        "nonce": nonce.hex()
                    }

                    original_bytes += len(raw_bytes)
                    encrypted_bytes += len(ciphertext)
                    parsed_count += 1

                except (OSError, ValueError, TypeError) as error:
                    failed_count += 1
                    if failed_count <= 5:
                        print("Skipped:", entry.name, "-", error)

                if parsed_count in checkpoints:
                    # Repeat queries to reduce timer noise.
                    lookup_times = []
                    correctness = []

                    for word in QUERIES:
                        expected = reference.get(word, set())
                        token = make_token(word, hmac_key)

                        durations = []
                        actual = set()

                        for _ in range(100):
                            start = time.perf_counter()
                            found = set(index.get(token, []))
                            durations.append(
                                (time.perf_counter() - start) * 1000
                            )
                            actual = found

                        lookup_times.extend(durations)
                        correctness.append(actual == expected)

                    # Time authenticated decryption of up to 20 documents.
                    decrypt_times = []
                    for doc_id in list(manifest.keys())[:20]:
                        item = manifest[doc_id]
                        nonce = bytes.fromhex(item["nonce"])
                        ciphertext = (
                            ENC_DIR / item["file"]
                        ).read_bytes()

                        start = time.perf_counter()
                        plaintext = aes.decrypt(nonce, ciphertext, None)
                        decrypt_times.append(
                            (time.perf_counter() - start) * 1000
                        )

                        if not plaintext:
                            raise RuntimeError("Unexpected empty email.")

                    overhead = (
                        (encrypted_bytes - original_bytes)
                        / original_bytes * 100
                        if original_bytes else 0
                    )

                    row = {
                        "documents": parsed_count,
                        "index_build_seconds": round(index_seconds, 6),
                        "encryption_seconds": round(encryption_seconds, 6),
                        "mean_lookup_ms": round(
                            statistics.mean(lookup_times), 6
                        ),
                        "mean_decryption_ms": round(
                            statistics.mean(decrypt_times), 6
                        ),
                        "original_bytes": original_bytes,
                        "ciphertext_bytes": encrypted_bytes,
                        "ciphertext_overhead_percent": round(overhead, 3),
                        "correct_queries": sum(correctness),
                        "total_queries": len(correctness),
                        "failed_files": failed_count
                    }
                    results.append(row)

                    print("\nCheckpoint:", parsed_count, "emails")
                    for name, value in row.items():
                        print(f"{name}: {value}")

            if parsed_count >= max(SIZES):
                break

    with RESULTS.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys())
                                if results else ["documents"])
        writer.writeheader()
        writer.writerows(results)

    (OUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    (OUT / "keyword_index.json").write_text(
        json.dumps(index), encoding="utf-8"
    )

    print("\nExperiment complete.")
    print("Emails processed:", parsed_count)
    print("Files skipped:", failed_count)
    print("Results CSV:", RESULTS)
    print("Encrypted files:", ENC_DIR)

    if parsed_count < max(SIZES):
        print(
            "WARNING: The largest requested checkpoint was not reached. "
            "Check the skipped-file count and available dataset."
        )


if __name__ == "__main__":
    main()
