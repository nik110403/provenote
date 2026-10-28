# Pipeline (Python)

Rebuild everything: `uv run python run_all.py` (or `python3 run_all.py`).

- `src/NN_*.py` run in numeric order; the runner stops at the first failing step and logs timestamps.
- `data/raw/` is read-only by convention; enforce it with `chmod -R a-w data/raw`; record every file in `data/raw/MANIFEST.md`.
- `output/figures/`, `output/tables/` hold stable filenames the paper refers to; renames are breaking.
- Ingested tables carry `source_sha256` and `retrieved_at` columns; validate schemas before writing.

| exhibit | script |
|---|---|
| `output/tables/demo_sum.csv` | `src/01_demo.py` |
