
from pathlib import Path
from email import policy
from email.parser import BytesParser
import csv

PROJECT = Path(r"C:\Users\sarag\SRE_Project")
SAMPLE = PROJECT / "data" / "sample"
OUTPUT = PROJECT / "data" / "processed"
CSV_FILE = OUTPUT / "emails.csv"


def extract_email(file_path):
    with open(file_path, "rb") as f:
        message = BytesParser(policy=policy.default).parse(f)

    body = message.get_body(preferencelist=("plain",))
    body_text = body.get_content() if body else ""

    # Handle messages that do not have a multipart body.
    if not body_text and not message.is_multipart():
        try:
            body_text = message.get_content()
        except (TypeError, ValueError):
            body_text = ""

    return {
        "message_id": str(message.get("Message-ID", "")),
        "date": str(message.get("Date", "")),
        "sender": str(message.get("From", "")),
        "recipient": str(message.get("To", "")),
        "subject": str(message.get("Subject", "")),
        "body": body_text,
    }


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    files = sorted(SAMPLE.glob("email_*.txt"))

    if not files:
        print("No sample emails found. Check the data/sample folder.")
        return

    rows = []
    errors = 0

    for file_path in files:
        try:
            row = extract_email(file_path)
            row["source_file"] = file_path.name
            rows.append(row)
        except Exception as error:
            errors += 1
            print(f"Could not parse {file_path.name}: {error}")

    columns = [
        "source_file",
        "message_id",
        "date",
        "sender",
        "recipient",
        "subject",
        "body",
    ]

    with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    print("Sample files found:", len(files))
    print("Emails parsed:", len(rows))
    print("Parsing errors:", errors)
    print("CSV saved to:", CSV_FILE)

    if rows:
        print("\nExample subject:", rows[0]["subject"])
        print("Example sender:", rows[0]["sender"])


if __name__ == "__main__":
    main()
