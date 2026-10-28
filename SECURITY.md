# Security policy

## Reporting a vulnerability

Report privately through GitHub: open the repository's **Security** tab and choose
**Report a vulnerability** (a private security advisory). Please do not open a public
issue for a suspected vulnerability.

## In scope

- The helpers in `plugins/provenote/bin/` that read local files and run `pandoc`
  or `pdftotext` (for example path handling, argument handling, unsafe file writes).
- The pipeline runner, which executes project code with your permissions. Reports
  about it being run on untrusted projects are welcome, but running a pipeline on
  code you do not trust is unsafe by design.
- Anything in the repository that leaks secrets or private data.

## Out of scope

- Behaviour of your assistant's model (Claude Code, Codex or another), including
  prompt injection through documents you ask it to read.
- Vulnerabilities in `pandoc`, `pdftotext`, Python or other third-party software;
  report those upstream.
- Quote checks accepting text that someone with write access to the project edited;
  see [what is verified](docs/verification.md).
