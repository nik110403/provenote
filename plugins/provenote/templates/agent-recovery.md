# Agent-guided environment recovery

Use these instructions during setup and after an operational failure. They are
instructions for the user's agent, not a guaranteed self-healing installer or a
background daemon. Existing user permissions still govern every action.

## Diagnose before changing anything

1. Preserve the exact failed command, working directory, exit status and full
   error output. Run the bundled `doctor --workflow pdf|build|word|all` (choose
   one workflow; add `--json` for structured findings) from the project root.
   If it is not on PATH, use the quoted absolute path to the intended kit's
   `bin/doctor` with `python3` on macOS/Linux or `py -3` in PowerShell.
2. Doctor checks only the selected prerequisites: `pdftotext` for PDF extraction,
   pandoc for builds, and Python 3.9+ only for Word checks. The optional Word
   demonstration also builds documents and therefore needs the `build` workflow.
   Check OCR/decryption tools separately only when that input requires them.
   A command-not-found error is an environment failure, not a quotation mismatch.
3. Check the installed helper path and adapter contents against the intended
   checkout. An identical adapter needs no reinstall. A stale PATH or session
   may point to another copy; prefer the intended absolute, quoted helper path.
   The Codex installer accepts an identical installation and refuses a differing
   destination. Never overwrite a differing adapter; report the difference and
   ask the user how to preserve or replace it.

## At most two repair attempts per problem

Choose the smallest environment-only fix supported by the diagnosis. Use the
user's existing install rights and permitted package manager to install a
missing dependency, select an available Python 3.9+ interpreter, or correct a
session-local PATH. Do not escalate privileges or bypass a permission prompt.
If approval is required, stop and request that approval with the proposed action.
No broad/destructive configuration changes, paid services or autonomous daemon.

For each stable doctor finding ID: propose the smallest fix, obtain any approval
required by existing permissions, apply only that approved fix, then rerun doctor
for the same workflow. Doctor only prints suggestions; it never applies them.
Only after the setup finding clears, retry the **exact failed command**, with the
same arguments and working directory; record any explicit interpreter/path correction. Check
its output and exit status, including per-file skips: a zero exit alone does not
establish that every input was processed. Never hide failures or skips.

If verification was affected, also run a small known-good and known-bad smoke
check in a fresh scratch directory, never against edited user research. From a
checkout, `python3 scripts/smoke.py` checks a good quote and HTML build (requires
`pandoc` and `pdftotext`); it does not test rejection. The bundled
`python3 examples/word/RUN.py --out <new-directory>` checks both a clean Word
quotation and a fabricated quotation (requires `pandoc`). On Windows use
`py -3` or the confirmed Python command. With installed assets only, use scratch
fixtures for the affected installed verifier: require a known-good match to pass
and a deliberately wrong quote to fail. If that check cannot run, report it as
unverified, never as a pass.

After at most two repair attempts per finding, stop if it remains unresolved. Report the exact
error, command/runtime/paths, both attempted fixes and their results, remaining
skips or unverified checks, and one concrete next action for the user.

## Research integrity is outside the repair loop

Never edit notes, a manuscript, source PDF/Markdown, hashes, manifests or CSV source/page
mappings to make a check pass. Never change verification code or thresholds,
weaken strictness, suppress errors, or turn a failed check into a skipped check.
A quotation/source mismatch or missing binding is a research result. Report it
and ask the human to confirm the mapping or supply the correct source; do not
infer reference identity or automatically rewrite the quote or its evidence.
Never reclassify a verification FAIL as a setup finding, even if doctor reports
an unrelated setup issue. A healthy doctor result does not certify research.
