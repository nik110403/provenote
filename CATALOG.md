# Component catalog

All components live in [plugins/research-kit/](plugins/research-kit/). There are
no second component trees or root command aliases. Follow [INSTALL.md](INSTALL.md)
when copying a subset: a skill folder can contain required assets, and scaffold
tools resolve templates relative to their own file location.

## Eight skills

Skills are instructions for an assistant, not standalone executables. Outputs
below are workflow artifacts; the main session saves model-returned text.

| Skill | Inputs → outputs | Dependencies and selective use |
|---|---|---|
| [new-research-project](plugins/research-kit/skills/new-research-project/SKILL.md) | Target directory and question → numbered project tree and filled project kernel | Python 3.9+, `new-project`, `templates/project/`; use for a new, empty target |
| [literature-search](plugins/research-kit/skills/literature-search/SKILL.md) | Research brief and queries → search CSV, Markdown, receipt; optional BibTeX | `lit-search`, Python, internet; optional Semantic Scholar key and `LIT_SEARCH_MAILTO`; use independently of PDF/note stages |
| [pdf-to-markdown](plugins/research-kit/skills/pdf-to-markdown/SKILL.md) | PDFs → source Markdown and manifest | `pdf2md`, Python, `pdftotext`; optional OCR/decryption; use for local sources |
| [literature-notes](plugins/research-kit/skills/literature-notes/SKILL.md) | Source Markdown, citekey, reading scope → `01_notes/lit/<citekey>.md`, quote-check results | Full folder including [template.md](plugins/research-kit/skills/literature-notes/template.md), `source-reader`, `verify-quotes`; use on already-converted sources |
| [review-against-notes](plugins/research-kit/skills/review-against-notes/SKILL.md) | Draft and literature notes → dated review report | `verify-quotes`, `check-claims`, `claim-checker`, `skeptic`; `check-bib` is a useful separate check, not included in this skill's sequence |
| [paper-build](plugins/research-kit/skills/paper-build/SKILL.md) | `10_paper/paper.md`, metadata, bibliography → bibliography findings, PDF, HTML or DOCX, log | `check-bib`, `build-paper`, Python 3.9+, pandoc; optional Typst/XeLaTeX; use on a prepared draft |
| [analysis-pipeline](plugins/research-kit/skills/analysis-pipeline/SKILL.md) | Pipeline target, language and data → pipeline skeleton, run report, figures/tables | `new-pipeline`, matching templates, `pipeline-runner`, Python or R; optional `uv`/`renv`; trust project code before execution |
| [tribunal](plugins/research-kit/skills/tribunal/SKILL.md) | A costly artifact or decision → sealed multi-lens review, verbatim transcript, `report.md` in `tribunals/<date>-<slug>/` | `tribunal-scribe`, `tribune`, `refuter`, Python 3.9+, git; for high-stakes calls only, not routine edits; the panel procedure is instructions, the record tool is the part that runs |

## Six agent roles

These are Claude-format role contracts. Copying them to another assistant does
not automatically configure its permissions or model. See [adapters](docs/adapters.md).

| Role | Inputs → returned output | Dependencies and selective use |
|---|---|---|
| [source-reader](plugins/research-kit/agents/source-reader.md) | One source path, citekey, optional scope → one note with claims and page-pinned quotes | Read-only source access; literature-notes `template.md`; caller saves and runs `verify-quotes` |
| [claim-checker](plugins/research-kit/agents/claim-checker.md) | Draft, cited sentences/keys, notes → supported/partial/not-supported/not-assessed rows and counts | Read-only draft/notes; judges notes only, not outside knowledge or source files |
| [skeptic](plugins/research-kit/agents/skeptic.md) | Draft and notes → evidence-anchored objections to three strongest claims | Read-only draft/notes; use after mechanical and support checks |
| [tribune](plugins/research-kit/agents/tribune.md) | Artifact path, frozen hash and one lens → verdict with severity-ranked, evidence-backed findings | Read-only; used by the `tribunal` skill in panels of at least three distinct lenses |
| [refuter](plugins/research-kit/agents/refuter.md) | One finding and artifact paths → REFUTED, STANDS or UNVERIFIABLE with evidence | Read-only, no shell; one finding per call; used by the `tribunal` skill |
| [pipeline-runner](plugins/research-kit/agents/pipeline-runner.md) | Trusted pipeline directory → PASS/FAIL, warnings, changed outputs | Read and shell execution; Python or R, optional `uv`; no agent edits, but executed pipeline writes outputs |

## Eleven tools

All helpers are Python 3.9+ programs (standard library only). Each supports `--help`. Invoke by explicit path
from the working directory indicated in [INSTALL.md](INSTALL.md).

| Tool | Inputs → outputs | Dependencies and selective use |
|---|---|---|
| [new-project](plugins/research-kit/bin/new-project) | Empty target directory → copied research project | Python; `templates/project/` sibling to `bin/`; refuses nonempty targets |
| [lit-search](plugins/research-kit/bin/lit-search) | Query/options or DOI export → ranked CSV, Markdown, receipt, optional `.bib` append | Python, internet to OpenAlex/Semantic Scholar/doi.org; optional API key; inspect provider status, never call a partial run complete |
| [pdf2md](plugins/research-kit/bin/pdf2md) | PDF paths/options → `<stem>.md`, manifest | Python, `pdftotext`; optional `ocrmypdf`, `qpdf`; `--engine docling` is refused (removed in 0.1.3: one page-1 block breaks page pinning); existing conversions need `--force` to overwrite |
| [verify-quotes](plugins/research-kit/bin/verify-quotes) | Notes naming source Markdown, pages and text → per-quote PASS/FAIL, nonzero on failure | Python; offline; checks text against page markers with whitespace/hyphenation normalization |
| [check-claims](plugins/research-kit/bin/check-claims) | Pandoc-cited draft and note directory → citation-to-note table | Python; offline; needs `verify-quotes` in the same folder; verifies quotes of each cited note, does not judge entailment |
| [check-bib](plugins/research-kit/bin/check-bib) | Bibliography and draft → duplicate/missing-field/DOI/citation findings | Python; offline; syntax/coverage checks do not verify bibliographic truth |
| [build-paper](plugins/research-kit/bin/build-paper) | Paper directory with Markdown and optional metadata → PDF/HTML/DOCX and `build.log` | Python 3.9+, pandoc, optional Typst/XeLaTeX and `pdftotext`; guard checks unresolved citations, missing files and `???`; avoid `--soft` for final validation |
| [new-pipeline](plugins/research-kit/bin/new-pipeline) | Empty target and `--lang python` or `--lang r` → copied pipeline | Python to scaffold; `templates/pipeline/` sibling to `bin/`; Python or R to execute result |
| [check-docx](plugins/research-kit/bin/check-docx) | Word file, notes root and a quote-to-source mapping → inventory CSV and bindings check | Python; offline; see the [Word workflow](docs/word.md) |
| [doctor](plugins/research-kit/bin/doctor) | Workflow name (`pdf`, `build`, `word`, `all`) → read-only setup diagnostics | Python; see [doctor](docs/doctor.md) |
| [tribunal-scribe](plugins/research-kit/bin/tribunal-scribe) | Tribunal workspace and per-turn payload files → verbatim, hash-chained `transcript.md` | Python and git (inside a git repository); only writer of the tribunal record; `verify` checks local consistency, `--expect-head` a retained head |

## Templates and examples

| Asset | Inputs → outputs | Dependencies and selective use |
|---|---|---|
| [Project template](plugins/research-kit/templates/project/) | Project question → instructions, task/progress files, source/note/code/output directories, bibliography and paper starter | Copy the whole template or use `new-project`; merge instructions rather than overwrite an existing project |
| [Python pipeline](plugins/research-kit/templates/pipeline/python/) | Numbered `src/NN_*.py` steps and raw data → stable `output/` artifacts | Python 3.9+, optional `uv`; [README](plugins/research-kit/templates/pipeline/python/README.md), `pyproject.toml`, runner, demo and manifest bundled; no environment lock is pre-generated |
| [R pipeline](plugins/research-kit/templates/pipeline/r/) | Numbered `src/NN_*.R` steps and raw data → stable `output/` artifacts | R; [README](plugins/research-kit/templates/pipeline/r/README.md), runner, demo and manifest bundled; initialize/snapshot `renv` yourself if needed |
| [Note template](plugins/research-kit/skills/literature-notes/template.md) | Source/citekey/read scope → claims and quoted-text front matter | Keep inside the literature-notes folder; reusable manually |
| [Basic example](examples/basic/RUN.md) | Bundled papers/conversions/notes → 14 positive checks and one planted failure | Python for offline checks; [source licenses](examples/basic/SOURCES.md) |
| [Search example](examples/search/RUN.md) | Search question → documented search walkthrough | Live search needs network; fixture-based tests are offline |

Raw-data freezing, provenance columns and environment locks are workflow
conventions to implement in your project, not guarantees supplied by scaffolding.
Licenses and early-stage limits are in [README.md](README.md) and [LICENSING.md](LICENSING.md).
