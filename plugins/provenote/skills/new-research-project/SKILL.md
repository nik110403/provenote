---
name: new-research-project
description: Create a new research project directory (numbered folders, task list, progress log, bibliography, project CLAUDE.md). Use when the user wants to start a paper, essay, or literature study from scratch.
---

Requires: Python 3.9+.

# New research project

Scaffold a project with the bundled tool. It copies a fixed template and refuses to
touch a target directory that already has content.

During setup and on operational failure, follow
`../../templates/agent-recovery.md` relative to this skill directory: at most two
environment-only repair attempts within existing permissions, then report.
An occupied target is not an environment fault; never clear it as a repair.

1. Ask where the project should live if the user has not said. Never pick a path inside
   an existing project. Before first use, run `doctor --workflow word` from the
   existing parent directory of the target: scaffolding, like Word checks, needs
   only Python's standard library. Use the intended kit's quoted `bin/doctor`
   path with `python3` (or `py -3` in PowerShell) if it is not on PATH. Follow the
   recovery guide for findings before creating the project; do not require
   pandoc or pdftotext just to scaffold.
2. Run:

   ```
   new-project <target-dir>
   ```

   If `new-project` is not on PATH, run it from the kit's plugins/provenote/bin/.

3. If it exits non-zero because the target is not empty, report that and ask for another
   path. Do not delete or overwrite anything.
4. Open `<target-dir>/CLAUDE.md` and fill in the project kernel (the one question the
   project answers) together with the user.
5. Tell the user the next stage: put PDFs in `02_sources/`, then convert, take notes, and
   verify quotes.

Layout created: `00_admin` (task list with a Resume-here block, progress log),
`01_notes` (open questions), `02_sources`, `03_code`, `05_figures`, `06_tables`,
`07_references` (empty `references.bib`), `10_paper`.
