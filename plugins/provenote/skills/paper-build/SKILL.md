---
name: paper-build
description: Build the paper from 10_paper/paper.md with pandoc citations to PDF or HTML, and check the bibliography. Use when the user wants to compile, cite-check or tidy the .bib of a research paper project.
---

Requires: Python 3.9+; pandoc (Typst or XeLaTeX optional for PDF).

# Paper build

On operational failure, follow `../../templates/agent-recovery.md` relative to
this skill directory: at most two environment-only attempts within existing
permissions, then report. Quote, citation and source failures require human
research decisions; never weaken the guard or rewrite evidence as recovery.

Layout: `10_paper/paper.md` (abstract, introduction, literature, data, method, results, discussion,
conclusion), `10_paper/metadata.yaml` (title, author, date, bibliography path). No CSL file is
bundled: pandoc's default citation style is used; drop a `.csl` into `10_paper/` and add `csl:` to
`metadata.yaml` to change it.

1. Check the bibliography first, from the project root:

   ```
   check-bib
   ```

   If not on PATH, run it from the kit's plugins/provenote/bin/. It reports duplicate keys,
   entries missing author/title/year, malformed DOIs, keys cited but absent (error) and keys
   present but uncited (note). Exit 1 on any error.
2. Build:

   ```
    python3 "/absolute/path/to/plugins/provenote/bin/build-paper" --to pdf
   ```

    Use an absolute, quoted path (PowerShell: `python` or `py -3`). It logs tool versions,
    runs `pandoc --citeproc`, and writes the requested PDF, HTML or DOCX without a mislabeled fallback.
     PDF prefers Typst then XeLaTeX, otherwise it explicitly writes HTML. The compile guard fails on
     literal `???`, unresolved citations and missing image/include files. `--grounding` opt-in runs
     local quote/claim checks but is not proof of the full draft; `--soft` downgrades failures for hooks.
     For DOCX, optional `--reference-doc /path/to/reference.docx` applies pandoc styles and document
     properties without changing the template. The result is a static, one-way export with static
     citations, not a live Zotero document or a round-trip editor; see [Word export](../../../../docs/word-export.md).
3. Fix each reported problem at its source; never silence the guard.

Bib discipline: one `.bib` per project, ideally exported by the reference manager. Verify author,
year, title and venue against the DOI landing page or the PDF before adding an entry; an entry
that cannot be verified is not written. Citekeys are stable once cited.
