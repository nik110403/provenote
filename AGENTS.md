# research-kit setup guidance

For Codex setup and project-local skill discovery, start with the
[official Codex skills documentation](https://developers.openai.com/codex/skills/).

## Use this collection in a project

To use research-kit in an existing project, follow the [Codex adapter section in
INSTALL.md](INSTALL.md#codex-adapter). It installs or copies only
`.agents/skills/research-kit/` into that project. Inspect an existing destination
first: do not overwrite or nest it, and do not replace the project's `AGENTS.md`,
instructions, configuration, or permission policy. This collection does not grant
permissions or create independent review.

Markdown instructions can be copied without Git or Python. Python 3.9+ is required
only to run the bundled research helpers; follow the prerequisite guidance in
INSTALL.md before invoking them.

## Contribute to this repository

Repository contributors edit and validate this checkout, following
[CONTRIBUTING.md](CONTRIBUTING.md). That is different from installing the adapter
into a user's project. Do not treat this file as permission to change user files or
settings.
