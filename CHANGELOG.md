# Changelog

## 0.2.0

### Renamed

The project is now **Provenote** (plugin ID, marketplace and repository: `provenote`; formerly
`research-kit`). The old repository URL redirects, but plugin and marketplace IDs do not. To
migrate in Claude Code:

```text
/plugin uninstall research-kit@research-kit
/plugin marketplace remove research-kit
/plugin marketplace add nik110403/provenote
/plugin install provenote@provenote
```

Skills and agents are now namespaced `provenote:` instead of `research-kit:`. For Codex, delete the
old `<project>/.agents/skills/research-kit/` folder and install the adapter again into
`<project>/.agents/skills/provenote/` ([INSTALL.md](INSTALL.md#upgrading-from-research-kit)); invoke it
as `$provenote`. Scripts that call `plugins/research-kit/bin/...` must use `plugins/provenote/bin/...`.
The denylist environment variable for `scripts/leak-check.sh` is now `PROVENOTE_DENYLIST` (default file
`~/.config/provenote/denylist`).

### Changed
- README restructured around install, a demo and a 30-second example; the full tool table is folded
  into a collapsible section. [INSTALL.md](INSTALL.md) gains an "Install the external tools" section.

### Fixed

- `check-docx` and `build-paper` no longer crash on Windows consoles with a non-UTF-8 code page when
  printing text such as CJK quotation marks; output is now always UTF-8.
- `check-docx` reports unsupported or ambiguous Word quotation coverage instead of silently treating it
  as verified, including quote paragraph styles and additional Word content types.

### Added

- Animated README and landing-page demo built from one real Claude Code run on a small demo project
  (`assets/demo-light.svg`, `assets/demo-dark.svg`); `tools/demo/` holds the captured transcript, the
  stdlib-only renderer and the fixture, so it can be regenerated.
- `scripts/install-deps.sh` (macOS Homebrew, Debian/Ubuntu apt, Fedora dnf) and `scripts/install-deps.ps1`
  (Windows winget, Chocolatey fallback) install Poppler and pandoc, optionally Typst, then run `doctor`;
  `--dry-run` / `-DryRun` previews. CI runs them in dry-run mode.
- GitHub Pages landing page under `site/` and a `pages` workflow that assembles and deploys it.
- `SECURITY.md` (how to report a vulnerability).
- `.github/RELEASE_NOTES_TEMPLATE.md` for release notes.
- `tribunal` skill, `tribune` and `refuter` agents, and the `tribunal-scribe` tool: a sealed, multi-lens
  review of a costly decision with a verbatim, hash-chained record. Ported from the
  [ai-architecture](https://github.com/nik110403/ai-architecture) collection; the record tool and its
  tests run, the panel procedure is instructions for the assistant.
- `build-paper --to docx --reference-doc PATH` applies a user-maintained pandoc style reference without
  changing it; [Word export](docs/word-export.md) documents this one-way output and its limits.
- The portable smoke test now exports a styled DOCX and runs the no-Zotero Word binding demonstration in
  every Windows, macOS and Linux CI cell. Native platform tests remain documented separately where they
  are still pending.

## 0.1.3

### Breaking changes (upgrading from 0.1.2)

`verify-quotes` (notes that passed under 0.1.2 may fail now; fix the note, not the check):

- A quote needs at least 5 words (15 characters if it contains CJK). Quote more text.
- The note's `citekey` must equal its file name. Rename the file or fix `citekey`.
- `source_md` must be the file `<citekey>.md`, directly in `02_sources/md/`, and the md's `source:`
  PDF name must also equal the citekey. Rename the md or PDF, or fix the fields.
  Lookups relative to the note's folder or the current directory are removed.
- A note with claims but no quotes now fails. Add quotes, or for a source that cannot be quoted
  declare `source_md: none` with `no_source: <reason>`.
- The front-matter parser rejects wrapped lines and nested mappings instead of skipping them.
  Put each field on one line.
- Matching is on word boundaries, so a fragment inside a longer word no longer matches.
- An unhashed md (no `md_sha256`) only warns by default and fails under `--strict`. Reconvert with
  `pdf2md` (0.1.3 writes the hash) and use `--strict`.

`check-claims`:

- The output schema changed: `UNSUPPORTED`/`THIN` are replaced by `OK`/`NO-SOURCE`/`UNVERIFIED`/
  `UNCITED`/`UNSOURCED`, rows are per (paragraph, key), and there is a fifth `detail` column.
  Scripts that grep the old labels or count columns must be updated.
- It runs `verify-quotes` on every cited note; a claims-only note is `UNVERIFIED`. It must find
  `verify-quotes` in the same folder.
- A draft with no recognised citation exits 1.
- The notes folder is the single `01_notes/lit` candidate or `--root <project>`; several candidates
  exit 2. Pass `--root` in scripts.

`pdf2md`: `--engine docling` is refused (exit 1); convert with the default engine. An existing legacy
`manifest.csv` is rewritten with the new `md_sha256` and `converter` columns.

`lit-search --export-bib`: a colliding citation key is renamed (`key` plus `a`, `b`, ...) instead of the entry
being skipped; entries whose DOI is already present are still skipped.

### Added

- `source_md: none` with `no_source: <reason>` declares a source that cannot be quoted (software,
  data, print book); `check-claims` reports it as `NO-SOURCE`.
- `<!-- unsourced: <reason> -->` marks a draft block whose quotations are deliberately unsourced.
- Narrative citations (`@key`) are recognised alongside `[@key]`.
- `docs/lecture.md` adds a concise Word-lecture quickstart: Unix and native Windows Python
  commands, the reproducible `examples/word/RUN.py --out NEW-DIRECTORY` demonstration,
  installation of the Codex adapter into a fresh project, and the required user-selected
  `source_md`/`page` CSV mapping. It states the Word check's source-page-only scope and its
  absence of Zotero or prewritten-note requirements.

### Fixed

- `verify-quotes`: superscript and subscript digits are kept as distinct characters instead of being
  erased before matching, so `130⁹` no longer matches `130`, `10⁹` differs from `10³` and `H₂O₂` from `H₂O`.
  Superscript and subscript signs (`⁺ ⁻ ⁼ ⁽ ⁾ ₊ ₋ ₌ ₍ ₎`) are distinct too, and private-use characters
  U+E000\u2013U+E02F are replaced by U+FFFD (so they never equal a tokenised superscript/subscript; they do
  equal each other and a typed U+FFFD). The only tolerance: a source footnote
  marker (a superscript digit run) directly after sentence punctuation (`. , ; : ?`) or a closing double quote and
  followed by whitespace or the end of the text may be left out of the quote. A superscript glued to a letter,
  digit, `)`, `]` or `%` (`rates¹`, `m²`, `(1+r)²`) must be copied verbatim.
- `check-claims`: HTML entities are decoded only after comments and code are masked, so an
  entity-encoded `&lt;!-- ... --&gt;` is visible text and its citations are checked.
  URLs and emails are masked after decoding, so an entity-encoded space ends a URL; decoded line breaks and
  control characters become spaces and cannot forge report lines. Ellipsis pieces under three words in a
  quotation now match on word boundaries too (`... 13 ...` no longer matches inside `130`).

### Other changes

- New `docs/verification.md` states what is checked mechanically and what stays model judgment, with the known limits; linked from the README.
- README and INSTALL link the Word lecture quickstart and clarify its portability and adapter setup.
- README: dropped overclaiming wording; verification is described as page-pinned matching against a markdown copy of the source (hash enforced with `--strict`).
- CI and `make check` lint every `SKILL.md` (`scripts/lint-skills.py`: front matter, name = folder, existing paths); CI runs `claude plugin validate --strict` when the CLI is present.
- `tools/banner/fonts/OFL.txt` now says the fonts ship as WOFF2. Plugin version bumped to 0.1.3.
- `check-claims`: the notes folder is never chosen by position. New `--root <project>` names the project
  (notes = `<project>/01_notes/lit`). Without it, every `01_notes/lit` found in the draft's ancestors (lexical and
  physical path) and the current directory is a candidate; exactly one is used, none means "no notes", and more
  than one stops the run with exit 2 ("ambiguous notes folder ... pass --root <project>"). An enclosing project,
  or a stray `/tmp/01_notes/lit`, therefore makes check-claims ask for `--root` instead of trusting either folder.
  The current directory's ancestors count as candidates too, and a candidate that cannot be inspected
  (permissions) stops the run with exit 2. For a draft from someone else, or when running from a script,
  always pass `--root <your project>`; check the `notes:` stderr line otherwise.
  The notes folder used is printed to stderr (`notes: <path>`). `verify-quotes` rejects a note whose real path
  leads to a different project than its given path, and therefore a symlinked `01_notes/lit`
  (behaviour change: keep notes in real folders). Do not nest a project under a folder named `01_notes`.
  The source hash and manifest catch accidental edits; they do not protect against someone with write access
  to the project's own `02_sources/`.
- `check-claims`: draft-quote findings (UNCITED rows, and UNVERIFIED rows caused only by a quotation in
  the draft) are advisory by default: printed as `UNVERIFIED (advisory)` / `UNCITED (advisory)` with an
  `advisory:` line, exit 0. `--strict-quotes` makes them fail. Note-level failures still always exit 1.
- `verify-quotes`: the project root is the folder above the outermost `01_notes/` in the note's path (only
  path names are read, never folder contents, so planted folders cannot move it); a strict check of a note
  not under `01_notes/` fails. A source md in a subdirectory of `02_sources/md/` now fails in every mode.
  A note whose folder is a symlink leading outside the project is rejected (symlinked note folders are not
  supported); a symlinked `02_sources/` or `02_sources/md` still works.

## 0.1.2

- Cosmetic release, no behaviour change. Terminal-transcript images now wrap at
  word boundaries (`tools/banner/bin/make-banner`), the licensing map covers the
  banner fonts, and a duplicated sentence is gone from the README.

Documentation changes made between 0.1.1 and 0.1.2, released with 0.1.2:

- 2026-10-15: Documentation only. README restructured with banner, terminal
  transcript and plugin tables per the public repository template; `tools/banner`
  added for regenerating the images. Plugin version stayed 0.1.1 at that point.
- Expand collection documentation with a complete catalog, whole and selective
  installation, contributor guidance and non-Claude manual adapters.
- Clarify support assets, tool paths, template layout, review dependencies,
  Docling pagination and the limits of Windows test evidence.
- Correct the README's stale version reference to existing plugin version 0.1.1.
## 0.1.1

- UTF-8 handling for standalone Python tools, including Windows locale handling.
- Optional Semantic Scholar API-key support.

## 0.1.0

- Initial research-kit collection: seven skills, four agent roles, eight tools,
  project and Python/R pipeline templates, and research examples.
