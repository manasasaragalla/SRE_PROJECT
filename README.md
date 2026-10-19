# Secure Searchable Email Prototype

A Python-based prototype demonstrating keyword search over encrypted email data using **HMAC-SHA-256** for keyword tokens and **AES-256-GCM** for email encryption.

This project explores how searchable encryption can help users find relevant emails without searching directly through plaintext email files.

## Project Overview

Cloud storage makes email data easy to access, but storing sensitive emails in plaintext can expose private information. Encrypting emails protects their contents, but ordinary encryption prevents direct keyword searching.

This prototype combines encryption with a searchable keyword index to demonstrate a basic approach to this problem.

### Key Features

- **Email dataset preparation:** Extracts a sample of emails from the Enron email dataset.
- **Email parsing:** Extracts fields such as sender, recipient, date, subject, and body.
- **Secure keyword indexing:** Generates HMAC-SHA-256 tokens for searchable keywords.
- **Email encryption:** Encrypts email files using AES-256-GCM.
- **Secure search and retrieval:** Searches the keyword index and decrypts matching emails locally.
- **Performance evaluation:** Measures search correctness, lookup latency, encryption time, and storage overhead.
- **Scalability testing:** Evaluates the prototype at multiple dataset sizes.
- **Visualization:** Generates graphs from scalability results.
- **Security auditing:** Checks the presence of plaintext data, encrypted files, indexes, and key files.

## System Architecture

```text
             Enron Email Dataset
                      |
                      v
              Dataset Preparation
                      |
                      v
                 Email Parsing
                      |
              +-------+-------+
              |               |
              v               v
       Keyword Indexing   Email Encryption
              |               |
              v               v
       HMAC-SHA-256       AES-256-GCM
              |               |
              v               v
       Searchable Index   Encrypted Emails
              |               |
              +-------+-------+
                      |
                      v
               Keyword Search
                      |
                      v
             Matching Email IDs
                      |
                      v
             Local Decryption
                      |
                      v
             Retrieved Emails
```

## Technologies Used

- **Language:** Python
- **Cryptography:** `cryptography` Python library
- **Keyword tokenization:** HMAC-SHA-256
- **Email encryption:** AES-256-GCM
- **Data processing:** Python CSV and file-processing utilities
- **Visualization:** Matplotlib
- **Version control:** Git
- **Dataset:** Enron email corpus

## Project Structure

```text
SRE_Project/
├── .gitignore
├── README.md
├── prepare_dataset.py
├── parse_emails.py
├── build_index.py
├── encrypt_emails.py
├── search_emails.py
├── secure_search.py
├── evaluate_project.py
├── scalability_test.py
├── plot_results.py
├── security_audit.py
└── data/
    ├── raw/
    ├── sample/
    ├── processed/
    ├── secure_index/
    ├── encrypted_emails/
    └── scalability/
```

The `data/` directories contain datasets, intermediate files, indexes, encrypted emails, and cryptographic keys. These files are excluded from Git using `.gitignore`.

## Requirements

- Python 3
- pip
- The Enron email dataset
- The Python packages required by the scripts

Install the main cryptography dependency:

```bash
python -m pip install cryptography
```

For plotting, install Matplotlib if it is not already available:

```bash
python -m pip install matplotlib
```

## Dataset

The project uses the Enron email corpus, a publicly available collection of email messages.

Dataset source: [Carnegie Mellon University — Enron Email Dataset](https://www.cs.cmu.edu/~enron/)

Download and extract the dataset, then configure the data path expected by `prepare_dataset.py`.

The current prototype uses a 100-email sample for the main workflow and a separate scalability experiment that processes up to 5,000 emails.

## How to Run

Run the scripts from the project root directory in the following order.

### 1. Prepare the email sample

```bash
python prepare_dataset.py
```

Copies a sample of raw email files into the working sample directory.

### 2. Parse emails

```bash
python parse_emails.py
```

Extracts email metadata and content into a CSV file.

### 3. Build the searchable keyword index

```bash
python build_index.py
```

Tokenizes email content and generates HMAC-SHA-256 keyword tokens.

### 4. Encrypt the emails

```bash
python encrypt_emails.py
```

Encrypts the sample email files using AES-256-GCM and stores the associated metadata needed for retrieval.

### 5. Search emails

```bash
python search_emails.py
```

Runs keyword searches against the generated index.

### 6. Search and retrieve encrypted emails

```bash
python secure_search.py
```

Searches the index and retrieves matching email content through local decryption.

### 7. Evaluate the prototype

```bash
python evaluate_project.py
```

Tests search correctness and measures selected performance and storage metrics.

### 8. Run scalability experiments

```bash
python scalability_test.py
```

Runs experiments with different dataset sizes and records results.

### 9. Generate graphs

```bash
python plot_results.py
```

Generates graphs from the scalability results.

### 10. Audit project files

```bash
python security_audit.py
```

Checks the state of the project's plaintext, encrypted data, index, and key files.

**Important:** Run the scripts in the intended order and inspect their configuration before execution. Some scripts depend on files created by earlier steps.

## Experimental Results

The recorded scalability experiment produced the following results:

| Number of emails | Index build time | Encryption time | Average lookup latency | Ciphertext size overhead |
|---:|---:|---:|---:|---:|
| 100 | 0.041 s | 0.079 s | 0.000286 ms | 0.844% |
| 1,000 | 0.326 s | 1.067 s | 0.004004 ms | 1.020% |
| 5,000 | 2.654 s | 4.806 s | 0.014934 ms | 0.726% |

These are recorded measurements from the current local environment, not universal performance guarantees.

- The reported lookup latency measures in-memory index lookup and does not include complete disk access or end-to-end decryption.
- Ciphertext size overhead compares the original email bytes with encrypted email bytes; it excludes index, manifest, and key storage.
- The decryption measurements were sampled from different emails, so they should not be used to claim that decryption becomes faster as the dataset grows.
- Repeated trials and a more controlled experimental setup would be needed for stronger performance conclusions.

## Security Considerations

- AES-256-GCM provides authenticated encryption when used correctly with unique nonces for each encryption under a given key.
- HMAC-SHA-256 generates deterministic keyword tokens, allowing matching queries to find indexed terms.
- Deterministic keyword tokens can reveal search and keyword-frequency patterns. This prototype should not be assumed to provide complete leakage protection.
- The current design stores keys locally and is not a complete cloud key-management solution.
- Plaintext email samples and processed CSV files remain sensitive and should be protected.
- Never commit cryptographic keys, credentials, private emails, or other sensitive data to a public repository.
- `.gitignore` prevents specified untracked files from being added automatically, but it does not remove files that have already been committed.

## Limitations

This is an educational prototype, not a production-ready searchable encryption system.

It does not implement a complete cloud storage service, distributed key management, formal security proofs, access-control infrastructure, or comprehensive leakage analysis. Its design is inspired by the searchable-encryption concepts studied in the relevant research literature, but it is not an exact reproduction of any specific paper's protocol.

## Future Enhancements

- Integrate encrypted storage with OpenStack or another cloud platform.
- Improve key management and user authentication.
- Support more advanced queries and multi-keyword searches.
- Add a web interface for searching and retrieving emails.
- Evaluate query leakage and security under a defined threat model.
- Conduct repeated benchmarks with larger datasets.
- Compare the implementation against established searchable-encryption approaches.

## Author

Developed as an academic prototype to explore secure searchable data storage, applied cryptography, and performance evaluation.
