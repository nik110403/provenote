---
name: analysis-pipeline
description: Scaffold and run a reproducible analysis pipeline (numbered scripts, frozen raw data, stable outputs) and link its figures and tables into the paper. Use when the user wants to set up, run or document data analysis for a research project.
---

Requires: Python 3.9+ (uv recommended); R for the R variant.

# Analysis pipeline

1. Scaffold: `new-pipeline <dir> --lang python` (or `--lang r`). If not on PATH, run it from the kit's plugins/provenote/bin/.
2. Add steps as `src/02_*.py`, `src/03_*.py` ... (R: `.R`); they run in numeric order. One command rebuilds everything: `run_all.py` / `run_all.R`.
3. Run via the `pipeline-runner` agent. It executes arbitrary project code, so run only pipelines you trust. It reports PASS/FAIL, warnings and changed outputs; it never edits.

Conventions:
- Raw data is frozen (read-only is a convention; enforce it with `chmod -R a-w data/raw`): `data/raw/<source>/<YYYY-MM-DD>/`, bytes as received, one line per file in `data/raw/MANIFEST.md` (source, URL, retrieval date, licence, sha256).
- Outputs go to `output/figures/` and `output/tables/`. Filenames are references used by the paper; renames are breaking changes.
- One interchange format between stages and one writer per file. Parquet for intermediate data; CSV only for small human-read tables.
- Ingested tables carry `source_sha256` and `retrieved_at` columns; validate schemas before writing.
- Log with timestamps per step; the runner exits non-zero on the first failing step.
- A figure or table title states the finding; notes make it self-contained.

Link into the paper: link (symlink or copy-on-build), never hand-copy, the needed files from `output/figures/` and `output/tables/` into the project's `10_paper/` so the paper always shows the last pipeline run.

Replication checklist: README with an exhibit-to-script table; environment lock file (`uv.lock` / `renv.lock`); raw-data manifest; licence; a rehearsed clean rebuild from a fresh clone.
