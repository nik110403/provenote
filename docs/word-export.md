# Word export

`build-paper --to docx` produces a static Word copy of
`10_paper/paper.md`. It runs pandoc's citation processor and writes
`10_paper/paper.docx`; citations are rendered text, not a live Zotero link.
The export is one-way: edit the Markdown source and rebuild rather than editing
the generated document in place.

## Use a style reference

From the research project root, create a pandoc reference document, customize
its styles in Word or LibreOffice, then pass it to the build. Pandoc uses the
reference document's styles and document properties; it does not copy its text
into the paper.

```sh
pandoc -o reference.docx --print-default-data-file reference.docx
python3 "/absolute/path/to/plugins/provenote/bin/build-paper" --to docx --reference-doc reference.docx
```

On Windows PowerShell, create the file with `-o` rather than redirecting binary
standard output. Use `python` or `py -3` if that is the Python launcher on your
machine.

```powershell
pandoc -o reference.docx --print-default-data-file reference.docx
& py -3 "C:\absolute\path\to\plugins\provenote\bin\build-paper" --to docx --reference-doc reference.docx
```

`--reference-doc` accepts a file path relative to the directory where you invoke
the command, including paths with spaces or Unicode characters. It is valid only
with `--to docx`; the helper refuses a missing, non-file, or alias of either
`paper.docx` or `build.log` (including hard links and symbolic links) so that it
cannot overwrite the template. The reference file is read, not modified.

## Limits and checks

The DOCX is a delivery artifact, not a round-trip editing format or an in-place
manuscript editor. It does not create or synchronize live Zotero citations.
`--grounding` additionally runs local quote and claim checks, but remains an
advisory, scoped check rather than verification of every claim or of a reference
template's contents. For quote checks on an existing Word document, see the
[lecture quickstart](lecture.md).
