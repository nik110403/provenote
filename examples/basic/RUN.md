# Example run: PDF → markdown → note → verified quotes

This walks the kit's core loop on two open-access papers (CC BY 4.0, see `SOURCES.md`).
Run on 2026-10-09 with the kit at this commit. Everything below is reproducible from the
repo root except step 3, where an agent writes the notes.

## 1. Project skeleton

```sh
plugins/provenote/bin/new-project examples/basic
```

This creates the numbered directories, `CLAUDE.md`, `00_admin/TASKLIST.md`, `00_admin/progress.md`,
`01_notes/open_questions.md` and an empty `07_references/references.bib`.

## 2. Convert the PDFs

The PDFs were downloaded from the URLs in `SOURCES.md` into `02_sources/pdf/`.

```sh
plugins/provenote/bin/pdf2md examples/basic/02_sources/pdf/*.pdf --out examples/basic/02_sources/md/
```

Result (`02_sources/manifest.csv`):

| stem | pages | chars/page | method |
|---|---|---|---|
| lei2023financial | 14 | 3570.1 | pdftotext (one column) |
| kireyev2026pricebench | 19 | 3712.9 | pdftotext (two columns, default reading order) |

Both pages carry `<!-- page N -->` markers. Neither paper needed OCR. The two-column paper
came out in correct reading order without `--layout`.

## 3. Write one note per paper

In Claude Code, the `literature-notes` skill dispatches one `source-reader` agent per source.
The agent has Read/Grep/Glob only; it returns the note and the main session saves it:

- `01_notes/lit/lei2023financial.md`: full text, 6 claims, 6 quotes
- `01_notes/lit/kireyev2026pricebench.md`: full text, 6 claims, 8 quotes

The notes in this directory are the agents' output, saved unedited.

## 4. Verify the quotes

```sh
cd examples/basic
../../plugins/provenote/bin/verify-quotes --strict 01_notes/lit/*.md
```

Result: 14 of 14 quotes PASS, exit 0.

## 5. Negative check: a fabricated quote must fail

`01_notes/negative/lei2023financial.md` holds one invented quote, attributed to
a real source.

```sh
../../plugins/provenote/bin/verify-quotes --strict 01_notes/negative/*.md
```

Result: `FAIL lei2023financial.md: quote 1 (p. 1): text not found in source` (the only failure), exit 1.

## 6. Page pins checked against the PDFs

`verify-quotes` checks pages against the markdown's page markers. To check that those markers
match the PDF, three quotes were looked up directly in the PDF page with
`pdftotext -f N -l N <pdf> -`. All three were found on the pinned page.

| note | quote (start) | pinned page | found in PDF page |
|---|---|---|---|
| lei2023financial | "In non-eurozone countries, labor market flexibility is pivotal…" | 9 | 9 ✓ |
| kireyev2026pricebench | "…these LLMs behave as constants and are directly exploitable" | 4 | 4 ✓ |
| kireyev2026pricebench | "The capability results are cross-sectional associations…" | 8 | 8 ✓ |

Note: these are PDF page indices (1 = first page of the file), which can differ from the
page numbers printed on the paper.
