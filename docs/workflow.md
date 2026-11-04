# Workflow: from question to checked draft

Enter at any stage for which you have the inputs. The tools handle mechanical
checks; assistant roles return text for the main session to save. A successful
quote match does not establish that a draft's claim is supported.

| Stage | Inputs | Components | Artifacts |
|---|---|---|---|
| Scaffold | Question, new empty target | `new-project`, `new-research-project` | Numbered project directories, instructions, task/progress files, bibliography and paper starter |
| Search | Brief and queries | `lit-search`, `literature-search` | `01_notes/search/<date>-<slug>.{csv,md,receipt.json}`; optional append to `07_references/references.bib` |
| Acquire | Selected references and permission to use them | You | PDFs in `02_sources/pdf/`, with source/license records |
| Convert | PDFs | `pdf2md`, `pdf-to-markdown` | `02_sources/md/<stem>.md`, `02_sources/manifest.csv` |
| Read and verify | Source Markdown, citekeys, scope | `literature-notes`, `source-reader`, `verify-quotes` | `01_notes/lit/<citekey>.md`, per-quote check results |
| Draft | Checked notes and research results | Author, project paper template | `10_paper/paper.md`, `metadata.yaml`, bibliography |
| Review | Draft and notes | `review-against-notes`: `verify-quotes`, `check-claims`, `claim-checker`, `skeptic` | Caller-saved `00_admin/reviews/<date>.md` |
| Bibliography check and build | Draft, bibliography, metadata, figures | `paper-build`, `check-bib`, `build-paper` | Findings, `10_paper/paper.pdf` or `.html`, `build.log` |
| Analysis side track | Trusted project code and raw data | `new-pipeline`, `analysis-pipeline`, `pipeline-runner` | Pipeline skeleton, run report, `output/figures/` and `output/tables/` |

See [CATALOG.md](../CATALOG.md) for direct component links and
[INSTALL.md](../INSTALL.md) for paths and dependencies. Keep the research project
root as the working directory for default research commands; run analysis from
the pipeline directory. Link results into the paper through a deliberate build
step rather than treating a successful analysis run as a paper rebuild.

## Optional note field: tier

A literature note may carry `tier: primary | secondary | partisan` (or the emoji green, yellow, red
circles). Primary is documents, data and testimony; secondary is scholarship and journalism; partisan
is a camp's own outlet or advocacy. `source-reader` proposes it; `verify-quotes` rejects other values
and accepts notes without it.

## Evidence boundaries

Search receipts record provider status. A run that loses Semantic Scholar or
OpenAlex is partial, even if it returns useful papers. Exported BibTeX still needs
source verification; `check-bib` checks structure and citation coverage offline.

The usual `pdftotext`/OCR conversion emits `<!-- page N -->` markers for extracted
PDF pages. Those indices may differ from printed page numbers; verify important
pins and suspect OCR numbers against the PDF. Docling was removed in 0.1.3 and `pdf2md --engine docling`
is refused: it put its whole conversion in one block marked page 1, which is not original
pagination and cannot establish a PDF page pin.

`source-reader` reads one source and returns a note using the local template.
The caller saves it and runs `verify-quotes`. Keep `read_scope` honest: sections
or abstract-only readings cannot stand in for a full reading. A failed quote must
be corrected from the source, removed with dependent claims, or left unresolved;
paraphrasing it does not turn it into a verified quotation.

Review first verifies quotes, then maps citations to notes, then judges support
with `claim-checker`, and finally asks `skeptic` to challenge the strongest claims.
`check-claims` runs `verify-quotes` on each cited note and reports uncited or unverified claims; only the judgment step evaluates
support. `check-bib` is useful alongside review but is not invoked by the
review-against-notes skill. The author decides draft changes; reviewers return
findings rather than editing the draft.

The three reading/review roles are read-only. `pipeline-runner` runs arbitrary
project code with your permissions, and that code writes outputs. Frozen raw
data, provenance columns, locks and replication checks are project conventions
to enforce, not automatically supplied guarantees.

## Smallest reproducible example

The [basic example](../examples/basic/RUN.md) bundles two attributed papers,
conversions, notes and a fabricated negative quotation. Python alone can run
the 14 positive checks and the expected negative failure described in the
[README](../README.md). This tests local quote matching, not a fresh model
reading, network search, paper build or native assistant installation.
