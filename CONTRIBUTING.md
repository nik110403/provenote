# Contributing

Keep changes small enough to check against a concrete example. State the
component, expected behavior, actual result and a minimal reproduction. Use
synthetic or redistributable fixtures, not private papers, correspondence or data.

## Checks

From the repository root:

```sh
make check
```

This runs the Python unit tests, strict Claude plugin validation when the Claude
CLI is installed, the positive example quote check and the tree leak check.
A skipped plugin validation is not evidence that native installation works.
Also run the deliberate negative example from `examples/basic`:

```sh
python3 ../../plugins/provenote/bin/verify-quotes --strict 01_notes/negative/*.md
```

Exit **1** and a fabricated-quote FAIL are expected. Do not edit the fixture to
make it pass. For doc-only changes, check local links and command paths; for
behavior changes, add tests exercising the actual failure and rerun the suite.
Report what ran, including skipped dependencies and platform limitations.

## Privacy

Review diffs for home paths, host/account identifiers, private URLs, emails,
passwords, API keys and research material you cannot share. Public authorship
and the public project handle are attribution, not permission to add private
identifiers. Treat source documents, API payloads and logs as untrusted data.

The bundled gate can scan the working tree with
`bash scripts/leak-check.sh --tree`. In your own checkout, you may opt into the
commit hook with `git config core.hooksPath .githooks`. A private denylist can be
supplied through `PROVENOTE_DENYLIST`; never commit its contents. In a real
Git checkout, `bash scripts/leak-check.sh --history` checks history too. A clean
pattern scan is not a substitute for reviewing source provenance or secrets.

## Licensing and documentation

Code, skills, roles and templates use [MIT](LICENSE); `docs/` uses
[CC BY 4.0](LICENSE-docs). The root collection guides use MIT, matching the README.
Retain third-party attribution and record a source's redistribution license
before adding fixtures; see [LICENSING.md](LICENSING.md) and
[examples/basic/SOURCES.md](examples/basic/SOURCES.md).

Update [CATALOG.md](CATALOG.md) and [INSTALL.md](INSTALL.md) when dependencies or
layout change. Keep all components under `plugins/provenote/`; avoid duplicate
trees, root aliases and undocumented support files. Add unreleased changes to
[CHANGELOG.md](CHANGELOG.md) without inventing a release or platform claim.
Release notes start from [.github/RELEASE_NOTES_TEMPLATE.md](.github/RELEASE_NOTES_TEMPLATE.md).
