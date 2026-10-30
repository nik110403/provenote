# Provenote plugin

Turn a reading list into source-grounded notes, check a draft against them, and build a paper.

- **Reading list to notes.** Search the literature, convert PDFs to page-marked Markdown, and
  write structured notes in which every quote is checked against its page in the source.
- **Draft against notes.** Uncited and unverified claims in a draft are flagged.
- **Paper build.** Check the bibliography, then build PDF, HTML or DOCX.

No API key and no server: the skills, agents and tools run inside Claude Code. The
`literature-search` skill sends search queries to Semantic Scholar and OpenAlex and resolves
DOIs via doi.org; everything else works on local files. An optional contact email, if you
configure one, is sent to OpenAlex only.

## Install

```text
/plugin marketplace add nik110403/provenote
/plugin install provenote@provenote
```

## Contents

- Skills: `new-research-project`, `literature-search`, `pdf-to-markdown`, `literature-notes`,
  `review-against-notes`, `paper-build`, `analysis-pipeline`, `tribunal`.
- Agents: `source-reader`, `claim-checker`, `skeptic`, `pipeline-runner`, `tribune`, `refuter`.
- Tools in `bin/`, run only when the assistant calls them.

Full documentation, install guide and changelog: https://github.com/nik110403/provenote
