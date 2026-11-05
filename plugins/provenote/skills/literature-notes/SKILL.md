---
name: literature-notes
description: Write one literature note per source with page-pinned verbatim quotes, then verify every quote against the source text. Use when the user wants to read, summarise or extract claims from converted PDFs (source markdown) in a research project.
---

Requires: Python 3.9+; source markdown from the pdf-to-markdown step (with `<!-- page N -->` markers).

# Literature notes

One note per source at `<citekey>.md` in the notes folder (layout `notes`, default `01_notes/lit`). Template: `template.md` beside this SKILL.md.
Folder names come from an optional `provenote.json` in the project root (see docs/workflow.md); the defaults below are the default layout. Run the tools from the project root: `provenote.json` is read from the working directory (or `--root`) only, never from a folder above.
The project root is that folder when it holds `provenote.json`, or without one the folder above `01_notes/`; keep notes in real (non-symlinked) folders under it. Without a layout file, do not nest a project under a folder named `01_notes`. The source hash/manifest catches accidental edits; it is not protection against someone with write access to the project's own sources folder (layout `sources_md`, default `02_sources/md`).
Source markdown carries page markers of the form `<!-- page N -->`; quote pages refer to them.

1. Pick the source markdown file(s) in the sources folder (layout `sources_md`, default `02_sources/md`) and a citekey for each (match the bibliography, layout `bib`, default `07_references/references.bib`, if the entry exists).
2. For each source, delegate to the `source-reader` agent: one agent, one source, one note. It has no write access and treats source text as untrusted data; it returns the finished note as its final message. Save that message yourself to `<citekey>.md` in the notes folder. Parallel agents for several sources are fine.
3. Verify every note:

   ```
   verify-quotes --strict <notes folder>/*.md      # default 01_notes/lit/*.md
   ```

   If not on PATH, run it from the kit's plugins/provenote/bin/. It prints PASS/FAIL per quote and exits non-zero on any FAIL. A quote passes only if it has at
   least 5 words and appears in the source on the pinned page on word boundaries (whitespace and
   line-break hyphenation are ignored). A note with claims but no quotes fails; so does a front-matter
   line the parser cannot read, a `citekey` that differs from the file name, a `source_md` whose file
   name is not the citekey, or a source md edited after conversion.
4. For each FAIL, open the source at that page and fix the quote or its page, or delete the quote
   and any claim that depended on it. Never "fix" a quote by paraphrasing. Re-run until it exits 0.
5. Report `read_scope` for each note to the user; `abstract_only` and `sections` notes must not be cited as full readings.

For a source you cannot convert or quote (software, a dataset, a print book) write the note with
`source_md: none` and `no_source: <reason>`, claims allowed, no quotes: `check-claims` then shows NO-SOURCE
instead of failing. Quotes must be at least 5 words long. In the draft, a quotation that comes from no source (own interview,
translation, epigraph) goes under a line `<!-- unsourced: <reason> -->`; `check-claims` lists it as UNSOURCED.

Front matter fields: `citekey`, `source_md` (path relative to the project root), `read_scope`
(`full_text` | `sections` | `abstract_only`),
`claims[]`, `quotes[]` with `page` and `text`.
Write `text` as a double-quoted one-line string (escape inner quotes as `\"`); never wrap it over several
lines and never use flow-style lists (`quotes: [...]`; an empty `quotes: []` is fine).
