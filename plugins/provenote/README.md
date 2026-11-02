# Provenote plugin

Turn a reading list into source-grounded notes, check a draft against them, and build a paper.

- **Reading list to notes.** Search the literature, convert PDFs to page-marked Markdown, and
  write structured notes in which every quote is checked against its page in the source.
- **Draft against notes.** Uncited and unverified claims in a draft are flagged.
- **Paper build.** Check the bibliography, then build PDF, HTML or DOCX.

No API key and no server: the skills, agents and tools run inside Claude Code. The
`literature-search` skill sends search queries to Semantic Scholar and OpenAlex and resolves
DOIs via doi.org. The other tools work on local files, with exceptions listed in the privacy
policy: `pandoc` can download a remote image, bibliography or citation style that a paper links
to, and a pipeline runs your own code. Your assistant reads your notes and sources and sends them
to its model provider. An optional contact email, if you configure one, is sent to OpenAlex and to
no other service; it also appears in your session transcript and reaches your model provider. See the
[privacy policy](https://github.com/nik110403/provenote/blob/main/PRIVACY.md).

## Install

```text
/plugin marketplace add nik110403/provenote
/plugin install provenote@provenote
```

## Contents

- Skills: `new-research-project`, `literature-search`, `pdf-to-markdown`, `literature-notes`,
  `review-against-notes`, `paper-build`, `analysis-pipeline`, `tribunal`.
- Agents: `source-reader`, `claim-checker`, `skeptic`, `pipeline-runner`, `tribune`, `refuter`.
- Tools in `bin/`: readable Python scripts, run only when the assistant calls them. They call
  `pandoc`, `pdftotext`, `ocrmypdf`, `qpdf`, `typst`, `xelatex` and `git` where installed
  (`doctor` only checks versions).

Full documentation, install guide and changelog: https://github.com/nik110403/provenote
