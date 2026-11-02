# Privacy policy

Effective 2026-11-02. Applies to the Provenote plugin and its tools.

Provenote's author runs no server and receives nothing from the plugin: no telemetry, no
analytics, no accounts, no cookies. The plugin's tools write your data to your project folder,
where you can delete it at any time, and make short-lived copies in your system's temporary folder.
The optional contact email stays in your assistant's plugin settings. Your assistant also reads your
data and sends it to its model provider; see [Your assistant](#your-assistant).

## What leaves your machine

The plugin's one network tool is `lit-search`, used by the `literature-search` skill. It runs when
you ask for a search, or when your assistant decides a search fits your request; your assistant
writes the queries, and its permission settings decide whether it asks you first. Other network use
is listed under [Other network use](#other-network-use).

| Sent to | What is sent | When |
|---|---|---|
| [OpenAlex](https://openalex.org/) | Your search query and year filter, work IDs when snowballing, and the optional contact email below | Search, snowballing |
| [Semantic Scholar](https://www.semanticscholar.org/) | Your search query and year filter | Search |
| [doi.org](https://www.doi.org/) | The DOIs being exported; each may redirect to the DOI's registration agency, such as Crossref or DataCite, or to the publisher | BibTeX export |

Each service also sees your IP address and a generic `provenote-lit-search/1.0` user agent, and
handles what it receives under its own privacy policy. Provenote has no agreement with them.

Search queries can reveal what you are working on. On a sensitive project, set your assistant to
ask before each search and review the query, or do not search from that project.

## Contact email

Setting the `mailto` plugin option is optional. Lit-search sends the address to OpenAlex and to no
other service, and does not write it to the search receipt. Claude Code writes the configured
value into the `literature-search` skill text when the skill loads, so the address also appears in
your session transcript and reaches your model provider.

## Local files

Search results, receipts, notes, Markdown conversions and built papers are written to your project
folder. The plugin's tools do not upload them; your assistant reads them as described under
[Your assistant](#your-assistant). Two tools can make copies in your system's temporary folder,
which are normally deleted when the tool finishes: `pdf2md` while it converts an encrypted or
scanned PDF, and `pandoc` while `build-paper` makes a PDF. The `tribunal` skill has your assistant
save each judge's response to a scratch location outside the project. The plugin asks for no
passwords or API keys and reads none from the environment. If your system sets the standard proxy
variables, lit-search requests go through that proxy.

## Other network use

These happen outside `lit-search`:

- `build-paper` runs `pandoc`, which downloads a remote image your paper links to when it builds a
  PDF or DOCX, and, for any format, remote resources named by metadata fields such as `csl:`,
  `bibliography:` or `citation-abbreviations:`. A TeX distribution that installs missing packages
  on demand, such as MiKTeX, may download those too, and Typst downloads any `@preview` package that
  a raw Typst block imports.
- The `analysis-pipeline` skill runs your own project code with your permissions, so that code does
  whatever you wrote it to do. A pipeline run with `uv` can download the dependencies your project
  declares and a Python interpreter, and `renv::restore()` downloads R packages.
- When a required program is missing, your assistant may follow the plugin's repair guidance and
  install it with your package manager, which downloads it from that package source.
- The `paper-build` skill tells your assistant to check bibliography entries against the DOI landing
  page or the PDF. If your assistant uses a web tool for that, the publisher's site sees the request.

## Your assistant

Provenote runs inside an AI coding assistant such as Claude Code or Codex. What the assistant reads
for you, including your PDFs, notes and drafts, goes to its model provider under your agreement
with that provider. Provenote does not control that flow. Check that provider's policy before
working on sensitive material. The `tribunal` skill can ask for a judge from a different model
family on high-stakes decisions, which sends the material under review to that second provider.

## Installing and updating

Installing or updating the plugin downloads it from GitHub, under GitHub's privacy policy.

## Children

Provenote is not directed at children under 18.

## Changes and contact

Changes to this policy are recorded in this file's history and in the [changelog](CHANGELOG.md).
Questions: open an [issue](https://github.com/nik110403/provenote/issues). For a privacy or security
problem you would rather not post in public, use the private report described in
[SECURITY.md](SECURITY.md).
