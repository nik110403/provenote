---
name: pdf-to-markdown
description: Convert PDF sources to page-marked markdown (text extraction with OCR fallback for scans). Use when the user adds PDFs to 02_sources/pdf or you need to quote, search, or read a paper's text.
---

Requires: `pdftotext` (poppler); optional `ocrmypdf`, `qpdf`.

# PDF to markdown

Convert once, then read the markdown instead of the PDF: it is cheaper to read, greppable,
and every page starts with a `<!-- page N -->` marker so quotes can cite a page.

Before first use, run `doctor --workflow pdf` from the project root. If it is
not on PATH, invoke the intended kit's quoted `bin/doctor` path with `python3`
(or `py -3` in PowerShell). Resolve findings through the recovery guide below;
doctor prints proposed fixes but never installs or changes anything. OCR and
decryption tools are conditional on the input and are checked separately.

```
pdf2md 02_sources/pdf/*.pdf --out 02_sources/md/
```

If `pdf2md` is not on PATH, run it from the kit's `plugins/provenote/bin/`.

On operational failure, follow `../../templates/agent-recovery.md` relative to
this skill directory. Limit recovery to two environment-only attempts; never
edit source text, hashes or verification thresholds to obtain a pass.

What it does per PDF:

1. Runs `pdftotext` in reading order (`--layout` opts into `-layout`, which can interleave columns). If the mean characters per page is under the threshold
   (`--threshold`, default 200) the file is treated as a scan and run through
   `ocrmypdf --skip-text`, then extracted again.
2. Encrypted PDFs are decrypted with `qpdf` first.
3. `--engine docling` is refused: Docling has no per-page output, so quote page pins would be wrong.
4. Writes `<stem>.md` (LF newlines) with a YAML header (source name, sha256, pages, chars per page,
   method, converter, `md_sha256`) and appends a row to `02_sources/manifest.csv`. `md_sha256` hashes
   the markdown body; `verify-quotes` recomputes it, so a hand-edited conversion fails verification.
   Re-convert with `--force` instead of editing the markdown. The hash guards against accidental edits,
   not a determined forger: the md and manifest sit next to each other in the project.

An existing conversion is never overwritten; pass `--force` to redo it. If a needed program
(`pdftotext`, `ocrmypdf`, `qpdf`) is missing the tool says which one and moves on to the
next file; follow the recovery guide for a permitted installation, then rerun
the exact failed command and account for every skipped file.

When to read the markdown: for summaries, notes, search, and quote checking. Go back to the
PDF only for figures, tables that came out garbled, or when `method` shows `ocr` and a
number or quote looks suspect. Check `chars_per_page` in the header: a very low value means
the extraction is unreliable.
