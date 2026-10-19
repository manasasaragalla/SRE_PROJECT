
import os
import shutil
from pathlib import Path

PROJECT = Path(r"C:\Users\sarag\SRE_Project")
RAW = str(PROJECT / "data" / "raw" / "maildir")
SAMPLE = PROJECT / "data" / "sample"

def main():
    print("Dataset folder:", RAW)

    if not os.path.isdir(RAW):
        print("ERROR: Dataset folder not found.")
        return

    SAMPLE.mkdir(parents=True, exist_ok=True)
    copied = 0
    errors = 0

    # Extended-length paths preserve filenames ending in dots.
    raw_extended = "\\\\?\\" + RAW

    for person in os.scandir(raw_extended):
        if not person.is_dir():
            continue

        email_folder = os.path.join(person.path, "all_documents")

        if not os.path.isdir(email_folder):
            continue

        with os.scandir(email_folder) as entries:
            for entry in entries:
                try:
                    if not entry.is_file():
                        continue

                    # Read using the extended-length source path.
                    with open(entry.path, "rb") as source:
                        content = source.read()

                    destination = SAMPLE / f"email_{copied + 1:03d}.txt"
                    destination.write_bytes(content)
                    copied += 1

                    if copied >= 100:
                        break

                except OSError as error:
                    errors += 1
                    if errors <= 5:
                        print("Skipped:", entry.name, "-", error)

        if copied >= 100:
            break

    print("Emails copied:", copied)
    print("Errors:", errors)
    print("Sample folder:", SAMPLE)

if __name__ == "__main__":
    main()
