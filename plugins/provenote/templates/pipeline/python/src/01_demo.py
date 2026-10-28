"""Demo step: reads a tiny inline dataset and writes one table to output/tables/.

Replace with real steps: read from data/raw/ (read-only), write to output/.
"""
import csv
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "output" / "tables"
ROWS = [("a", 1), ("b", 2), ("c", 3)]

OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "demo_sum.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["key", "value"])
    w.writerows(ROWS)
print(f"wrote demo_sum.csv; total = {sum(v for _, v in ROWS)}")
