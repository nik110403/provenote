## provenote X.Y.Z

One or two sentences: what this release is for and who should upgrade.

### Highlights

-

### Breaking changes

Write "None" if there are none. Otherwise say what stops working and how to fix it.

-

### Added

-

### Fixed

-

### Install and upgrade

New install: follow the Install section of the repository README (Claude Code marketplace
route, or the Codex adapter in INSTALL.md).

Upgrade an existing install:

```text
/plugin marketplace update provenote
/plugin update provenote@provenote
```

For a release that renames the plugin or marketplace, replace this upgrade block with that
release's migration steps from CHANGELOG.md: the commands above fail for users of the old name.

External tools (Poppler, pandoc, optional Typst): see
INSTALL.md, section "Install the external tools (one command)".

### Verification evidence

What was checked for this release and what was not:
docs/verification.md in the repository.
Link the CI run for the release commit.
