# Lecture quickstart: checking typed Word quotations

Use this when a lecture already exists as a `.docx` with ordinary typed
author--year citations. `check-docx` reads that saved file and never edits it.
It uses neither Zotero nor prewritten Provenote notes.

## Install

Install the released version (0.2.0) as described in the
[README](../README.md#claude-code) or [INSTALL.md](../INSTALL.md).

To reproduce the demonstration below, clone the repository (see the [README](../README.md#30-second-example)) and, with Python 3.9+, run from its root.

On Unix-like systems, use `python3`; on native Windows PowerShell, use the
Python launcher as `py -3` (or `python` if that is your Python 3 command).
The helpers need Python 3.9+. The Word demonstration additionally needs
`pandoc` on `PATH`. No network service, model, or bibliography manager is
needed for either check.

## Reproduce the bundled Word demonstration

Choose a directory that does not yet exist; the demo refuses to overwrite it.

```sh
python3 examples/word/RUN.py --out /tmp/provenote-word-demo
```

```powershell
py -3 .\examples\word\RUN.py --out C:\Temp\provenote-word-demo
```

The retained output contains a clean document that passes and a fabricated
quotation that fails. The demo creates the bindings CSV itself only to make its
result reproducible; for a real lecture, choose every mapping yourself.

## Check a real lecture

First convert each source PDF to page-marked Markdown in the research project
that will supply the sources. Then inventory the lecture's supported
double-quoted passages into a *new* CSV:

```sh
python3 plugins/provenote/bin/check-docx \
  --root /absolute/path/to/research-project \
  --inventory /absolute/path/to/new-word-quotes.csv \
  /absolute/path/to/lecture.docx
```

Open that CSV. For each row, explicitly set `source_md` to the chosen path
under `02_sources/md/` and `page` to the positive page number where that exact
quotation occurs. Typed citations and references do not select a source or a
page for you. Save the completed CSV as a bindings file, then run:

```sh
python3 plugins/provenote/bin/check-docx \
  --root /absolute/path/to/research-project \
  --bindings /absolute/path/to/word-quotes.csv \
  --report /absolute/path/to/new-word-check \
  /absolute/path/to/lecture.docx
```

PowerShell uses the same arguments with Windows paths, for example
`py -3 .\plugins\provenote\bin\check-docx --root C:\research\project
--bindings C:\research\word-quotes.csv C:\research\lecture.docx`.

A `QUOTE_MATCH` says that one user-chosen quotation, source Markdown file and
page match. It is not a citation check, bibliography check, global verification
of the lecture, or proof that the source supports the lecture's claim. See the
[full Word workflow](word.md) for delimiters, coverage warnings and reports.

## Optional: install the Codex adapter in a fresh project

Create an empty project directory, then install the adapter from this checkout:

```sh
mkdir /absolute/path/to/fresh-project
python3 scripts/install-codex.py --project /absolute/path/to/fresh-project
```

```powershell
New-Item -ItemType Directory C:\path\to\fresh-project
py -3 .\scripts\install-codex.py --project C:\path\to\fresh-project
```

It copies the local adapter to `.agents/skills/provenote/` in that project.
The installer is idempotent only when the installed files are identical; it
refuses a differing destination. This installation does not establish live
Codex discovery or permissions.

## When setup or a command fails

Ask your agent to follow the packaged
[environment recovery guide](../plugins/provenote/templates/agent-recovery.md).
The Codex adapter and relevant Claude skills point to it during setup or runtime
failures. It permits two environment-only attempts, reruns the failed command,
and stops with an exact-error report if unresolved. It cannot guarantee automatic
repair and never changes research evidence or source/page mappings to pass a check.
