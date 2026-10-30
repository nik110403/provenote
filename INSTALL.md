# Installation: whole collection or selected parts

## Whole Claude Code plugin

In Claude Code, add the public marketplace and install its plugin:

```text
/plugin marketplace add nik110403/provenote
/plugin install provenote@provenote
```

This loads the packaged eight skills and six roles from the canonical
`plugins/provenote/` tree. It does not install Python, Poppler, pandoc, R or
optional dependencies. Do not replace your existing settings, `CLAUDE.md`,
`AGENTS.md` or permission policy with this collection's examples.

For predictable command paths, keep a checkout of
[Provenote](https://github.com/nik110403/provenote). In a POSIX shell **at
the checkout root**, set:

```sh
KIT="$(pwd)/plugins/provenote"
```

`KIT` below must remain an absolute path. Run `python3 "$KIT/bin/verify-quotes"
--help` to confirm the Python helper can launch. The plugin's instructions use
bare tool names: either add this directory for the current shell with
`export PATH="$KIT/bin:$PATH"` (and ensure executable permission), or explicitly
give your assistant the absolute tool path. A Markdown skill is not a PATH setup
mechanism; changing directories alone will not resolve a bare command.

## Upgrading from research-kit

Provenote was called research-kit before 0.2.0. An existing research-kit install stops loading
("Plugin research-kit not found in marketplace research-kit") as soon as its marketplace is
refreshed, by hand or by auto-update, because the marketplace now lists only `provenote`. Move to
the new name in Claude Code:

```text
/plugin uninstall research-kit@research-kit
/plugin marketplace remove research-kit
/plugin marketplace add nik110403/provenote
/plugin install provenote@provenote
```

For Codex, delete the old `<project>/.agents/skills/research-kit/` folder, then install the
adapter again into `<project>/.agents/skills/provenote/` as described in the Codex adapter
section below, and invoke it as `$provenote`.

If you followed an older guide and `/plugin install research-kit@research-kit` fails, the
marketplace you just added is already called `provenote`: run `/plugin install provenote@provenote`
instead.

## Install the external tools (one command)

The helpers need Poppler (`pdftotext`) and pandoc; Typst is optional for PDF output.
Reading or loading a skill does not execute any tool; tools run only when the assistant
calls them. Git is needed for the marketplace route above (the ZIP route in the
[Codex adapter](#codex-adapter) section needs none).

macOS (Homebrew), Debian/Ubuntu and Fedora:

```sh
bash scripts/install-deps.sh            # shows the commands, asks y/N
bash scripts/install-deps.sh --yes      # no prompt
bash scripts/install-deps.sh --typst    # also install Typst
bash scripts/install-deps.sh --dry-run  # preview only
```

Windows (PowerShell 5.1+; winget, falls back to Chocolatey):

```powershell
.\scripts\install-deps.ps1 [-Yes] [-Typst] [-DryRun]
```

Add `--workflow pdf|build` (`-Workflow`) to install only what one workflow needs. Tools
already on PATH are skipped. The script ends by running `doctor`, so a clean exit means
setup is complete. Homebrew is not installed for you; get it at <https://brew.sh>. On
other systems the script prints what to install by hand and exits 3. With `--typst`, only
Homebrew and the Windows managers install Typst; on apt and dnf the script prints a hint
instead, because `typst` is missing from many Debian/Ubuntu and Fedora repositories.

## Selective skills and roles

Choose dependencies from [CATALOG.md](CATALOG.md). Copy **the full skill folder**
into your project's `.claude/skills/`, not just `SKILL.md`. For example, from the
checkout root, after confirming `PROJECT` points to your intended project:

```sh
PROJECT="/absolute/path/to/your-project"
mkdir -p "$PROJECT/.claude/skills"
cp -R "$KIT/skills/literature-notes" "$PROJECT/.claude/skills/"
```

Before copying, inspect the destination: if that skill already exists, back it
up and reconcile changes rather than nesting or overwriting it blindly. Notes
also need `template.md`, the `source-reader` role and `verify-quotes`.

For Claude roles, copy selected `.md` files to your project's `.claude/agents/`
under the same names, with the same collision precautions. For example:

```sh
mkdir -p "$PROJECT/.claude/agents"
cp "$KIT/agents/source-reader.md" "$PROJECT/.claude/agents/"
```

Alternatively, read a role as a manual contract and provide its task to an
assistant; that does not create a native agent or enforce permissions. Review
needs `claim-checker` and `skeptic` as well as `verify-quotes` and `check-claims`.
A tribunal needs `tribune`, `refuter` and `tribunal-scribe` (and a git repository for the workspace).
Analysis needs `pipeline-runner`; running project code is a separate trust decision.

## Selective tools and templates

Python helpers, including `build-paper`, run with `python3` and an absolute file
path, without PATH or executable permissions. On Windows PowerShell use `python`
(or `py -3`) and a quoted absolute path.

Most helpers can be copied alone, except that `check-claims` needs `verify-quotes` in the same folder. **The two scaffold tools cannot:** retain this
layout wherever you put them, selecting only the needed template subtree:

```text
chosen-kit/
  bin/new-project
  bin/new-pipeline
  templates/project/          # needed by new-project
  templates/pipeline/python/  # needed for --lang python
  templates/pipeline/r/       # needed for --lang r
```

`templates/` is a sibling of `bin/`, not inside it. Keep the entire selected
template subtree. Do not flatten the scaffold scripts into an unrelated PATH
directory without those templates.

### Run commands from the right directory

With `KIT` set above, switch your shell to the research **project root** before
using defaults for notes, bibliography, search output and `10_paper/`:

```sh
python3 "$KIT/bin/lit-search" "your research question" --since 2015 --n 25
python3 "$KIT/bin/pdf2md" 02_sources/pdf/*.pdf --out 02_sources/md/
python3 "$KIT/bin/verify-quotes" 01_notes/lit/*.md
python3 "$KIT/bin/check-docx" --root /absolute/path/to/project --inventory /absolute/path/to/new-word-quotes.csv /absolute/path/to/lecture.docx
python3 "$KIT/bin/check-claims" 10_paper/paper.md
python3 "$KIT/bin/check-bib"
python3 "$KIT/bin/build-paper" --to pdf
```

Each line is an independent stage; run only what you selected. Search writes
files and uses network; conversion writes a manifest and source Markdown;
build writes an artifact/log. Checking quotes, claims and bibliography is offline.
Keep note `source_md` paths relative to the research project root.

Scaffolding takes explicit targets and refuses nonempty ones:

```sh
python3 "$KIT/bin/new-project" /absolute/path/to/new-paper
python3 "$KIT/bin/new-pipeline" /absolute/path/to/new-pipeline --lang python
```

Run the generated pipeline **from its own directory** using `python3 run_all.py`
(or `uv run python run_all.py`), or `Rscript run_all.R` for the R variant.
The generated project instructions are a starting point for a new project,
not a replacement for instructions in an existing one.

## Platform and dependency checklist

Python 3.9+ covers the eleven helpers. `pdf2md` additionally needs `pdftotext`
from Poppler; optional `ocrmypdf` handles scans and `qpdf` encrypted PDFs. Docling was removed in 0.1.3: `pdf2md --engine docling` is refused
because its output is one block marked page 1, which breaks page pinning. Search uses OpenAlex, Semantic Scholar and doi.org.
`lit-search` reads no API keys or contact details from the environment (urllib's standard proxy
variables still apply), so Semantic Scholar is queried anonymously and often returns 429/403; inspect receipts for partial provider coverage.
An optional contact email for OpenAlex is the plugin setting `mailto` (`/plugin configure
provenote@provenote` in Claude Code), which the skill passes as `--mailto`; elsewhere, pass
`--mailto <your-address>` yourself.

Model steps (the skills and roles) depend on your assistant's access and may incur
its usual costs. CI covers the helpers on Linux, macOS and Windows, not a live Codex
session; no native non-Claude integration and no cross-platform performance guarantee
is claimed. Running a pipeline executes project code with your permissions.

`build-paper` needs Python 3.9+ and pandoc on PATH. It prefers Typst then XeLaTeX
for PDF, and explicitly writes HTML if neither engine exists; use `--to html` or
`--to docx` to select a format. On Windows PowerShell, for example:

```powershell
$provenoteKit = (Resolve-Path .\plugins\provenote)
python "$provenoteKit\bin\verify-quotes" --strict 01_notes/lit/lei2023financial.md
python "$provenoteKit\bin\build-paper" --to html
```

For a static DOCX export styled with a pandoc reference document, see the
[Word export walkthrough](docs/word-export.md). It covers Unix and PowerShell
commands, template creation, and the one-way/static-citation limits.

### Codex adapter

Install one self-contained Codex skill into an existing project; it does not alter
`AGENTS.md`, global configuration, or the Claude plugin. The skill is discovered
from `<project>/.agents/skills/provenote/`, so use a project you intend Codex to
work in.

#### No Git or Python: copy with a file manager

On GitHub, choose **Code → Download ZIP**, extract the archive, and open its
`provenote` folder in your file manager. In the project where you use Codex,
create `.agents`, then `skills` inside it (enable hidden files first if `.agents`
is not visible). Create the final `provenote` folder once, so the result is:

```text
<project>/.agents/skills/provenote/
  SKILL.md
  bin/
  templates/
  agents/
  workflows/
```

Copy `docs/codex/SKILL.md` from the extracted repository into that final folder and
name it `SKILL.md`. Copy `bin/`, `templates/`, and `agents/` from
`plugins/provenote/` alongside it. Finally copy the **whole**
`plugins/provenote/skills/` folder there and rename that copied folder
`workflows/`. Do not copy a folder named `provenote` into the final
`provenote` folder: that creates redundant nesting and prevents the expected
layout.

Before copying, stop if `<project>/.agents/skills/provenote/` already exists.
Back it up and compare it; do not overwrite a destination or instructions you did
not inspect. Restart Codex after copying, then explicitly ask: `$provenote show
me the available Provenote workflows; do not run helpers yet.` This checks skill
discovery only. It does **not** prove that research helpers work.

Copying or loading these Markdown instructions needs no Python. Python 3.9+ is
needed only when actual research helpers run. Do not run `doctor` until Python is
available and its launcher is confirmed.

#### Optional Python installer

If Python 3.9+ is already available, this convenience installer builds the same
layout and retains its safe behavior: it accepts an identical destination and
refuses a differing one. Git is not required if you extracted a ZIP:

```sh
python3 scripts/install-codex.py --project /absolute/path/to/project
```

```powershell
python .\scripts\install-codex.py --project C:\path\to\project
```

The installed skill is `.agents/skills/provenote/`. Set `$provenoteKit` to that
path when prompting Codex to run a clean quote demo. R and any analysis packages belong to the chosen
pipeline environment; `uv` and `renv` are optional environment-management tools.

#### Before running helpers

Python is optional for installation, but required for every bundled research helper.
If it is missing, use the official [Windows installer](https://www.python.org/downloads/windows/)
or [macOS installer](https://www.python.org/downloads/macos/). On Debian or Ubuntu,
run `sudo apt update && sudo apt install python3`; on Fedora, run `sudo dnf install
python3`. Close and reopen the terminal, then check `python3 --version` on Linux or
macOS, or `py -3 --version` / `python --version` in PowerShell. Confirm it reports
Python 3.9 or newer before running doctor. If an older distribution supplies an
older Python, use a supported distribution release or the [official Python
downloads](https://www.python.org/downloads/) and check again. Only then run the
installed `bin/doctor` for the workflow you plan to use. PDF conversion and paper
builds have additional optional dependencies (such as Poppler, pandoc, Typst, or
XeLaTeX); install them only for those workflows.

Try the [offline quote check](README.md) before adding network or build
dependencies. Other-assistant adaptation is described in [docs/adapters.md](docs/adapters.md).

### Word lecture quickstart

For a saved `.docx` with typed quotations, see the [lecture quickstart](docs/lecture.md).
It distinguishes `python3` on Unix-like systems from `py -3`/`python` on native
Windows, runs the bundled Word demonstration in a new output directory, and
has the explicit inventory-to-CSV source/page mapping required for a real
lecture. This workflow uses neither Zotero nor prewritten notes; its result is
only a match against each user-chosen source page, not a citation, bibliography
or global-document check.
