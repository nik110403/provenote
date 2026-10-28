---
name: provenote
description: Source-grounded research workflows with installed, local Python helpers.
---

# Provenote for Codex

This skill is self-contained. Its installed directory is
`<project>/.agents/skills/provenote`. In shell examples, set `provenoteKit` to
that directory. Its `bin/` and `templates/` directories must remain siblings.
Use actual quoted paths, never bare helper names or `CLAUDE_PLUGIN_ROOT`.

Use `$provenote` only as the Codex skill trigger, not as a shell variable. In a
POSIX shell, for example, set `provenoteKit="/absolute/path/to/.agents/skills/provenote"`.
In PowerShell, set `$provenoteKit = "C:\absolute\path\to\.agents\skills\provenote"`.

On macOS/Linux use `python3 "$provenoteKit/bin/verify-quotes" ...`. In PowerShell
use `& python "$provenoteKit\bin\verify-quotes" ...` (or `& py -3` if `python` is not
available). The copied workflows in `workflows/` and role contracts in `agents/`
are instructions, not imported permissions. If independent roles are unavailable,
run their steps serially and label the result non-independent.

During setup and on any operational failure, read and follow
`templates/agent-recovery.md` relative to this installed skill directory. If Python
is absent, report that prerequisite and use the installation guide before trying
`doctor`; it requires Python. The recovery guidance allows at most two
environment-only repair attempts using existing permissions, then requires an
exact-error report. Research mismatches are not repair targets.

Useful local checks:

```text
python3 "$provenoteKit/bin/verify-quotes" --strict 01_notes/lit/*.md
python3 "$provenoteKit/bin/check-claims" --root . 10_paper/paper.md
python3 "$provenoteKit/bin/build-paper" --to html
python3 "$provenoteKit/bin/check-docx" --root /absolute/path/to/project --inventory /absolute/path/to/new-word-quotes.csv /absolute/path/to/lecture.docx
```

On PowerShell, pass explicit note paths instead of relying on shell glob expansion:

```powershell
& python "$provenoteKit\bin\verify-quotes" --strict 01_notes/lit/example.md
& python "$provenoteKit\bin\build-paper" --to html
& python "$provenoteKit\bin\check-docx" --root "C:\research\project" --inventory "C:\research\new-word-quotes.csv" "C:\research\lecture.docx"
```

`build-paper --grounding` runs local quote and citation checks, but it is not proof
of a complete draft. Canonical workflow command examples use the installed helper
paths above; consult the copied `workflows/` folders for their full assets.

For static DOCX output, `build-paper --to docx --reference-doc <path>` uses a
pandoc style reference document. For template creation and its
one-way/static-citation limits, read `docs/word-export.md` in the downloaded
Provenote repository; that walkthrough is not bundled in this installed skill.

For an ordinary Word lecture, use `$provenote` to request the Word workflow.
Run `check-docx --inventory`, then have the user explicitly confirm every
`source_md` and page in the new CSV before `--bindings`. Never ask an LLM to
infer reference identity from typed citations or to make that integrity judgment.
