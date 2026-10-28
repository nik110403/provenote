#!/usr/bin/env python3
"""Create and check ordinary typed-citation Word examples, offline."""

import csv, hashlib, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CHECK = REPO / "plugins/provenote/bin/check-docx"


def run(args, want):
    p = subprocess.run(args, text=True, capture_output=True)
    print(p.stdout, end="")
    print(p.stderr, end="", file=sys.stderr)
    if p.returncode != want:
        raise SystemExit(f"expected exit {want}, got {p.returncode}")


def make(name, page, out):
    doc = out / f"{name}.docx"
    inv = out / f"{name}-inventory.csv"
    bindings = out / f"{name}-bindings.csv"
    subprocess.run(["pandoc", "-o", str(doc), str(HERE / f"{name}.md")], check=True)
    before = hashlib.sha256(doc.read_bytes()).hexdigest()
    run(
        [
            sys.executable,
            str(CHECK),
            "--root",
            str(out / "project"),
            "--inventory",
            str(inv),
            str(doc),
        ],
        0,
    )
    rows = list(csv.DictReader(inv.open(encoding="utf-8")))
    for r in rows:
        r["source_md"], r["page"] = "02_sources/md/lei2023financial.md", str(page)
    with bindings.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    run(
        [
            sys.executable,
            str(CHECK),
            "--root",
            str(out / "project"),
            "--bindings",
            str(bindings),
            "--report",
            str(out / name),
            str(doc),
        ],
        0 if name == "clean" else 1,
    )
    assert hashlib.sha256(doc.read_bytes()).hexdigest() == before
    subprocess.run(
        ["pandoc", "-t", "plain", str(doc)], check=True, stdout=subprocess.DEVNULL
    )


def main():
    if len(sys.argv) != 3 or sys.argv[1] != "--out":
        raise SystemExit("usage: RUN.py --out NEW-DIRECTORY")
    out = Path(sys.argv[2]).resolve()
    if out.exists():
        raise SystemExit("--out must be new")
    if not shutil.which("pandoc"):
        raise SystemExit("pandoc is required for this demo")
    (out / "project/02_sources/md").mkdir(parents=True)
    shutil.copy2(
        REPO / "examples/basic/02_sources/md/lei2023financial.md",
        out / "project/02_sources/md/",
    )
    shutil.copy2(
        REPO / "examples/basic/02_sources/manifest.csv", out / "project/02_sources/"
    )
    make("clean", 2, out)
    make("fake", 2, out)
    print(f"demo retained at {out}")


if __name__ == "__main__":
    main()
