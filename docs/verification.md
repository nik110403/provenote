# What Provenote verifies, and what it leaves to judgment

Provenote separates two kinds of checking. The command-line tools check text mechanically,
with no model and no network. Everything about meaning is judgment, by a model or by you.

The mechanical claim is narrow: **every quote is matched, on a stated page, against a hashed
markdown copy of the source.** (The hash is enforced by `verify-quotes --strict`, or when the
manifest records it; without either, a missing hash is only a warning.) It does not say the quote is accurate to the original PDF, that
it supports the claim it is attached to, or that the claim is true.

## Mechanical checks

### `verify-quotes` (notes against sources)

For each note it checks:

- **Quote text.** A quote needs at least 5 words (15 characters for a quote containing CJK
  characters). It must occur on the page the note pins it to, on word boundaries, in the source markdown
  (`02_sources/md/<citekey>.md`, with `<!-- page N -->` markers). Matching normalises Unicode
  (NFKC), whitespace, line-break hyphenation, typographic quotes and dashes, soft hyphens and
  non-breaking spaces; nothing more. Superscript and subscript digits and signs (`⁺ ⁻ ⁼ ⁽ ⁾ ₊ ₋ ₌ ₍ ₎`) are kept
  as distinct characters, never equal to plain ones, in both quote and source (`130⁹` does not match `130`,
  `10⁹` is not `10³`, `H₂O₂` is not `H₂O`, `Ca²⁺` is neither `Ca⁺` nor `Ca+`). Private-use characters
  U+E000\u2013U+E02F are replaced by U+FFFD (so they never equal a tokenised superscript/subscript; they do
  equal each other and a typed U+FFFD). The one tolerance is for
  footnote markers on the source side only: a superscript digit run directly after sentence punctuation
  (`. , ; : ?`) or a closing double quote and followed by whitespace or the end of the text may be left out of the
  quote. A superscript glued to a letter, digit, `)`, `]` or `%` (`rates¹`, `m²`, `R²`, `(1+r)²`) must be
  copied verbatim.
  A quote found only on another page fails ("text found on a different page").
- **Hashed source.** When the source md records `md_sha256` (written by `pdf2md`), the body is
  re-hashed; an edit after conversion fails. `--strict` requires the hash, and when
  `02_sources/manifest.csv` has an `md_sha256` column it must match the md.
- **Names agree.** The note's `citekey` must equal its file name, and `source_md` must be the
  file `<citekey>.md` sitting directly in `02_sources/md/` (not a subfolder); the md's `source:` PDF name must also equal the citekey. A note with claims
  needs quotes. A source that cannot be quoted (software, data, print book) is declared with
  `source_md: none` plus `no_source: <reason>`; such a note may not have quotes.
- **Fail-closed note parsing.** The front matter is read by a small strict parser. A line it
  cannot consume (wrapped text, nested mappings, flow-style `claims`/`quotes` lists, tab
  indentation, duplicate keys) is an error, never skipped. A misspelled-keys note with no quotes,
  claims or source is rejected as empty.
- **Project boundary.** The project root is the folder above the outermost `01_notes/` in the
  note's path; only path names are read. A note whose real path leads outside the project or to a
  different project is rejected, so symlinked note folders are not supported. A strict check of a
  note not under `01_notes/` fails.

Exit code: 0 when every check passes, 1 on any FAIL, 2 on usage error.

### `check-claims` (draft against notes)

It finds pandoc citations in a draft and maps each key to `<project>/01_notes/lit/<key>.md`,
running every cited note through the `verify-quotes` checks. It prints one row per
(paragraph, key):

- `OK`: the note exists, has quotes, and all of them verify.
- `NO-SOURCE`: the note declares a source that cannot be quoted.
- `UNVERIFIED`: no note, a note without quotes, or a failing note; also a quotation in the draft
  (4+ words) that no cited source holds verbatim, or an unbalanced quotation mark.
- `UNCITED`: a quotation (4+ words) in a paragraph with no citation.
- `UNSOURCED`: informational; the block follows `<!-- unsourced: <reason> -->`.

**Parsing order.** HTML entities are decoded only after comments and code are masked, so an
entity-encoded `&lt;!-- ... --&gt;` is visible text and its citations are checked.

**What a draft `OK` does not mean.** `check-claims` does not check page numbers in the draft:
`[@key, p. 999]` next to a genuine quote is `OK`. It also accepts any cited source in the paragraph as
the holder of a quotation, so attribution to the specific citation is not checked.

**Which notes folder.** With `--root <project>` the notes are `<project>/01_notes/lit`. Without it,
every `01_notes/lit` found in the draft's ancestors (lexical and physical path) and in the current
directory and its ancestors is a candidate. Exactly one is used; none means "no notes"; more than one stops the run
with exit 2. The folder used is printed to stderr as `notes: <path>`.

**Exit codes.** 1 if any note-level row is `UNVERIFIED` (no note, no quotes, failing note) or no
citation is recognised; 2 on usage error, an ambiguous notes folder, or a candidate that cannot be
inspected; 0 otherwise.

**Advisory vs strict.** Findings that come only from a quotation in the draft (`UNCITED`, and
`UNVERIFIED` rows caused only by a draft quotation) are heuristic. By default they print as
`UNVERIFIED (advisory)` / `UNCITED (advisory)` with an `advisory:` line and exit 0.
`--strict-quotes` makes them fail the run. Note-level failures always fail.

## Model judgment

These steps are done by a model (or by you) and are not machine-checked:

- Whether a verified quote actually supports the claim it is attached to (the `claim-checker` role).
- Summaries, extracted claims and the wording of notes.
- Draft review and critique (`review-against-notes`, `skeptic`).
- Choice of search terms, relevance of search results, and whether a source is worth reading.
- Unquoted paraphrase: `check-claims` does not judge it.

A passing `verify-quotes` run therefore means "these strings are on these pages of these source
copies", and a model's reading of what they mean still needs your review.

## Known limits

- **Other Unicode compatibility forms are folded.** Circled, fullwidth and mathematical digits, fractions
  and superscript letters such as `ⁿ` are folded to plain characters by NFKC on both sides, so a quote may
  use either form. Subscript letters (`xᵢ` = `xi`), squared-unit glyphs (`㎡` = `m2`) and `™` = `TM` fold too.
- **Footnote handling is all-or-nothing per quote.** Within one quote, copy every footnote marker
  verbatim or omit them all; a mix of copied and omitted markers does not match.
- **A footnote marker glued to the following text is not tolerated.** `ended.¹Then` must be copied verbatim.
- **A word split by a dash at a line end may not match** (pre-existing).
- **Ellipsis quotes match piece by piece.** Each piece is matched on word boundaries, in order, anywhere
  after the previous piece, so a quote stitched from scattered single words can pass. Keep ellipsis pieces long.
- **Write access defeats the hashes.** The source hash and manifest catch accidental edits. They
  do not protect against someone with write access to the project's own `02_sources/`, who can
  change a source and its hash together.
- **Drafts from someone else need `--root`.** For an external draft, or when running from a
  script, always pass `--root <your project>`; otherwise the folder choice depends on where the
  draft and the shell happen to be. Check the `notes:` stderr line.
- **Symlinked note folders are rejected.** Keep notes in real folders under `01_notes/`. A
  symlinked `02_sources/` or `02_sources/md` still works. Do not nest a project under a folder
  named `01_notes`.
- **The md is a conversion, not the PDF.** Page pins are only as good as the converter's page
  markers. `pdf2md` refuses `--engine docling` because it has no per-page output; if you convert
  a source some other way, check its page markers against the PDF.
- **Draft-quote checks are heuristic** and advisory by default (see above).
