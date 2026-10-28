---
name: review-against-notes
description: Review a draft against the project's literature notes - mechanical citation checks first, then model judgment, then an adversarial pass, ending in a dated review report. Use when the user wants a draft fact-checked against their notes before submission.
---

Requires: Python 3.9+; a draft with pandoc citations (`[@key]`) and literature notes in `01_notes/lit/` (see the literature-notes skill).

# Review against notes

Order matters: mechanical checks first, model judgment second, adversary last. Reviewers never edit the draft.

1. Verify quotes in every note:

   ```
   verify-quotes --strict 01_notes/lit/*.md
   ```

   If not on PATH, run it from the kit's plugins/provenote/bin/. Fix FAILs before going on.
2. Map citations to notes:

   ```
   check-claims [--strict-quotes] --root <project> <draft.md>
   ```

   Always pass `--root <your project>` (the folder that holds `01_notes/` and `02_sources/`) when you know it:
   for a draft from someone else, or when running from a script, a folder the draft ships with would otherwise
   be trusted. Without `--root` it looks for `01_notes/lit` in the draft's and the current directory's ancestors;
   more than one, or an unreadable folder, stops the run with exit 2. It prints `notes: <folder>` on stderr:
   check that this is your project's notes folder.

   If not on PATH, run it from the kit's plugins/provenote/bin/. It prints a markdown table:
   OK, NO-SOURCE, UNSOURCED, UNCITED, or UNVERIFIED with the reason (no note, a note without quotes, a quote that fails
   `verify-quotes`, or a quoted passage of 4+ words in the paragraph that no cited source holds verbatim;
   check ellipses, `[brackets]`, case, and that every quotation mark is closed). A quote is checked
   against the sources cited in its paragraph, so cite the paper the quote comes from.
   NO-SOURCE marks a software, dataset or print-book citation whose note says `source_md: none`; it is
   not a failure. Never drop such a citation: write a note with `source_md: none` and `no_source: <reason>`.
   It also exits non-zero if the draft has no recognisable citation (`[@key]` or narrative `@key`).
   UNCITED is a quotation (4+ words) in a block with no citation. A quotation that is not from any
   source (own interview, own translation, epigraph, hypothesis box) is exempted with a line
   `<!-- unsourced: <reason> -->` directly before its paragraph or blockquote; check-claims then lists it
   as UNSOURCED. The marker never exempts a citation: cited keys still need their note.
   Exit status: note-level failures (no note, a failing note, a note without quotes, no citation) always
   exit 1. Draft-quote findings (UNCITED, and UNVERIFIED caused by a quotation in the draft) rely on a
   heuristic quote extractor, so they are printed as `UNVERIFIED (advisory)` / `UNCITED (advisory)` with an
   `advisory:` line, and exit 0; pass `--strict-quotes` to make them fail. An advisory row is not a pass:
   read it and check the quotation by hand.
   Resolve note-level UNVERIFIED rows before the model passes: write or fix the note. Check advisory rows:
   fix the quote or cite the right source; use `<!-- unsourced: <reason> -->` only for a quotation that is
   genuinely not from any source (see above). Never delete a citation just to silence a quote row.
3. Delegate to the `claim-checker` agent with the cited sentences and keys. It judges each sentence against its note only
   (SUPPORTED / PARTIAL / NOT SUPPORTED / NOT ASSESSED, plus the quote relied on).
4. Delegate to the `skeptic` agent, which tries to refute the 3 strongest claims, each finding with an evidence anchor.
5. Save the report yourself to `00_admin/reviews/<date>.md` (create the folder). List findings as atomic rows
   `id | claim | verdict | evidence | fix` and end with counts that reconcile:
   supported + unsupported + not assessed = cited sentences checked.
6. Tell the user what is unsupported or partial. Do not edit the draft; the author decides.
