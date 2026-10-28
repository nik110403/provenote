# Pipeline (R)

Rebuild everything: `Rscript run_all.R` from this directory.

renv: run `renv::init()` once, install packages, then `renv::snapshot()` to write `renv.lock`.
On a fresh clone run `renv::restore()` before `run_all.R`. Commit `renv.lock`.

- `src/NN_*.R` run in numeric order; the runner stops at the first failing step and logs timestamps.
- `data/raw/` is read-only by convention; enforce it with `chmod -R a-w data/raw`; record every file in `data/raw/MANIFEST.md`.
- `output/figures/`, `output/tables/` hold stable filenames the paper refers to; renames are breaking.

| exhibit | script |
|---|---|
| `output/tables/demo_sum.csv` | `src/01_demo.R` |
