# Checking ordinary Word quotations

`check-docx` reads an existing saved `.docx`; it never changes it. It is for a
lecture or manuscript with ordinary typed author--year citations and references.
It does **not** use Zotero, Better BibTeX, a library export, or literature notes.

First inventory the supported double-quoted passages. Supported delimiters are
ordinary straight double quotes (`"…"`) and English curly double quotes
(`“… ”`). `--root` is required and selects the source collection, even when the
Word file is elsewhere.

```sh
python3 "/absolute/path/to/provenote/plugins/provenote/bin/check-docx" \
  --root "/absolute/path/to/project" --inventory "/absolute/path/to/new-word-quotes.csv" \
  "/absolute/path/to/lecture.docx"
```

Open the new CSV and explicitly fill `source_md` (a path below
`02_sources/md/`) and the positive source `page` for every row. You, not an
assistant, select that mapping. The checker does not infer it from typed
citations or references. Then verify, optionally creating fresh reports:

```powershell
& python "C:\absolute\path\to\provenote\plugins\provenote\bin\check-docx" `
  --root "C:\research\project" --bindings "C:\research\word-quotes.csv" `
  --report "C:\research\word-check" "C:\lecture.docx"
```

The source conversion's canonical hash and manifest are enforced, each mapped
quote must occur verbatim on its selected page, and source paths must resolve
inside `02_sources/md/`. `QUOTE_MATCH` means only that user-selected mapping
matches the converted source page; it is not a global citation, bibliography or
document-identity pass.

It reads body/table paragraphs and referenced positive footnotes/endnotes,
including text split across Word runs. Deleted text and tracked move-from content
are ignored; inserted and move-to text are included. Headers, footers, text boxes,
fields, embedded/altChunk content and
unsupported/unbalanced quote forms are coverage warnings and make the command
non-success rather than silently claiming coverage. Known unsupported quotation
delimiters that warn include guillemets (`«»`, `‹›`), German low/high marks
(`„‚`, `‟‛`), and CJK corner/double-corner marks (`「」`, `『』`, `〝〞〟`). The
checker does not claim to recognise every quotation or punctuation convention;
ordinary apostrophes attached to words (including plural possessives) remain usable.
Single-quote candidates, including unmatched candidates and pairs spanning a line
or paragraph, are coverage warnings; a word-final ASCII apostrophe without a known
single-quote opener remains conservatively ambiguous and is treated as a possessive.
Word's built-in `Quote` and `IntenseQuote` paragraph styles, including derived
styles and a single default paragraph style, are also reported as unextracted
coverage rather than verified quotations. Ambiguous multiple defaults warn rather
than guessing. Duplicate paragraph style IDs are likewise treated as ambiguous
coverage rather than allowing one definition to overwrite another. Inventory prints coverage
warnings as well as its count, and binding checks carry the same warnings into
their terminal output and reports. Outputs are new-only.
For spreadsheet safety, every CSV cell beginning with an apostrophe, `=`, `+`,
`-`, `@`, tab, or carriage return is prefixed with one apostrophe. The checker
reverses that prefix when it reads a bindings CSV (including Excel's UTF-8 BOM), so quote hashes and matching
always use the original text.

Run the bundled offline demonstration with `python3 examples/word/RUN.py --out
/tmp/provenote-word-demo`. It needs local `pandoc` but no network or model.
