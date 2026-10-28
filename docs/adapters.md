# Using the collection with other assistants

The native packaged route is the Claude Code plugin: eight skills and six
Claude-format roles. The command-line tools also run without any assistant.
For another assistant, distinguish **manual workflow adaptation** from **native
skill discovery**. Neither imports Claude's agent permissions automatically.

## Manual workflow and role adaptation

1. Choose a stage from the [catalog](../CATALOG.md). Read its `SKILL.md`, support
   assets and required role contracts from `plugins/provenote/`.
2. Give the assistant the actual project paths and absolute tool paths. Translate
   commands to the available terminal interface; run them from the research
   project root, or from the pipeline directory for `run_all.py` / `run_all.R`.
3. For source reading and review, preserve read-only roles, untrusted-source
   treatment, honest reading scope, evidence anchors and the returned-text
   contract. The main session saves notes/reports and runs mechanical checks.
4. If using `AGENTS.md` for project guidance, merge only the selected workflow
   rules into the existing file after reviewing it. Do not overwrite permissions
   or translate a Claude `tools:` front matter line into an assumed native API.

When no role-dispatch mechanism is available, a person can run separate reading
and review tasks using those contracts. Label this manual adaptation; do not
claim native agents or independently enforced read-only access. `pipeline-runner`
requires shell execution, and the pipeline may write outputs even though the
role itself does not edit code. Only execute trusted project code.

## Optional native skill discovery

Codex installation is tested as a local adapter; live Codex discovery has not been
tested. These are documented discovery paths:

| Assistant | Documented path | Source and evidence scope |
|---|---|---|
| OpenCode | Project `.opencode/skills/<name>/SKILL.md`; documented `.claude/skills/` and `.agents/skills/` equivalents also exist | [Official skills documentation](https://opencode.ai/docs/skills/) |
| Codex | `.agents/skills/<name>/SKILL.md`; repository guidance is read from `AGENTS.md` from root to cwd | [Official skills documentation](https://developers.openai.com/codex/skills/) |

The preparation review observed these official sources on **2026-10-14**.
This document records those supplied observations; this documentation pass did
not independently retrieve the pages or test native discovery. Recheck current
documentation before relying on a path in a different version.

For Codex, use `python3 scripts/install-codex.py --project <project-dir>` (or
`python .\scripts\install-codex.py --project <project-dir>` in PowerShell). It
copies a self-contained `.agents/skills/provenote/` with helpers, templates,
workflow assets and role contracts. It neither creates nor overwrites `AGENTS.md`.
Discovery makes instructions available; it does not import Claude permissions.

## Dependencies survive adaptation

- Use absolute, quoted helper paths and `python3` on macOS/Linux or `python`/`py -3`
  in PowerShell. Do not assume the plugin cache is on PATH.
- `new-project` and `new-pipeline` need `templates/` as a **sibling of `bin/`**.
  Moving only a script breaks its template lookup.
- Notes require the local note template, `source-reader` contract and
  `verify-quotes`. Review requires `verify-quotes`, `check-claims`,
  `claim-checker` and `skeptic`. `check-bib` remains a separate useful check.
  A tribunal requires `tribune`, `refuter` and `tribunal-scribe`.
- Agent `.md` formats, model names and permission declarations are not universally
  imported. Configure equivalent capabilities in the host assistant according to
  its documentation; otherwise use the contracts manually and disclose the gap.

The [install guide](../INSTALL.md) gives tool/dependency details. CI exercises
macOS, Linux and Windows helper paths; it does not provide live Codex evidence.

## Create a small, portable workflow

[Create your own](create-your-own.md) provides dependency-free starter skill,
Claude-agent, and portable role-contract templates. They are examples to copy and
adapt, not declarations of permissions or independent review.
