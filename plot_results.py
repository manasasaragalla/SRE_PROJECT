
import csv
from pathlib import Path
import matplotlib.pyplot as plt

PROJECT = Path(r"C:\Users\sarag\SRE_Project")
CSV_FILE = PROJECT / "data" / "scalability" / "scalability_results.csv"
GRAPH_DIR = PROJECT / "data" / "scalability" / "graphs"

GRAPH_DIR.mkdir(parents=True, exist_ok=True)

with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

if not rows:
    raise ValueError("No scalability results found.")

sizes = [int(r["documents"]) for r in rows]

def save_graph(values, title, ylabel, filename):
    plt.figure(figsize=(8, 5))
    plt.plot(sizes, values, marker="o")
    plt.title(title)
    plt.xlabel("Number of emails")
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(GRAPH_DIR / filename, dpi=200)
    plt.close()

save_graph(
    [float(r["index_build_seconds"]) for r in rows],
    "Index Construction Time vs Dataset Size",
    "Time (seconds)",
    "index_build_time.png",
)

save_graph(
    [float(r["encryption_seconds"]) for r in rows],
    "Encryption Time vs Dataset Size",
    "Time (seconds)",
    "encryption_time.png",
)

save_graph(
    [float(r["mean_lookup_ms"]) for r in rows],
    "Mean Keyword Lookup Latency vs Dataset Size",
    "Latency (milliseconds)",
    "lookup_latency.png",
)

save_graph(
    [float(r["ciphertext_overhead_percent"]) for r in rows],
    "Ciphertext Size Overhead vs Dataset Size",
    "Overhead (%)",
    "ciphertext_overhead.png",
)

print("Graphs saved to:", GRAPH_DIR)
for image in sorted(GRAPH_DIR.glob("*.png")):
    print(image.name)
