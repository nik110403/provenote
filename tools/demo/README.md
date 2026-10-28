# README demo (assets/demo-light.svg, assets/demo-dark.svg)

An animated SVG (about 18 s, plays once) built from one real Claude Code run. Every line drawn comes
from `transcript.jsonl`. One edit was made by hand after the capture: when the project was renamed
from research-kit to Provenote (0.2.0), the plugin name in the prompt ("Using the research-kit
plugin's bin tools" became "Using the provenote plugin's bin tools") and the sanitized path
(`~/research-kit/...` became `~/provenote/...`) were changed to match. Nothing else in the transcript was
changed; the original is in the repository history before 0.2.0.

## What it shows

In `fixture/` (a demo fixture, not part of `examples/basic`: one real note and source from that example
plus `10_paper/draft.md`, a short draft written for the demo with two planted flaws):

1. `verify-quotes --strict` passes the real note (6 of 6 quotes).
2. The planted fabricated note fails (`FAIL ... text not found in source`).
3. `check-claims` flags the draft's invented quote ("4 percent of GDP") and an uncited quotation.
4. Claude summarises which sentences the notes do not back.

## Capture

Date 2026-10-26, Claude Code 2.1.310, model `claude-opus-5-5[1m]`. One run, from the fixture directory:

```sh
cd tools/demo/fixture
claude -p --plugin-dir ../../../plugins/research-kit --output-format stream-json --verbose \
  --no-session-persistence --allowedTools "Bash" --max-budget-usd 1 "<prompt, first record of transcript.jsonl, with research-kit for provenote>"
```

The run predates the rename, so the plugin directory was still `plugins/research-kit`. The plugin was
loaded with `--plugin-dir`, so its `bin/` tools were on PATH. The run cost about 0.31 USD.

## Files

- `transcript.jsonl`: the capture reduced by `render.py extract` to prompt, `meta`, Bash commands, tool
  results and Claude's text. Dropped from the raw stream: hook output, thinking blocks, rate-limit and
  token events. Paths were sanitized to `~/research-kit/tools/demo/fixture`, then renamed to `~/provenote/...` (see above).
- `render.py`: stdlib-only; the prompt appears line by line (0.3 s each), commands are typed, output reveals line by line. `python3 -I render.py render transcript.jsonl ../../assets` writes both SVGs.
- `fixture/`: the demo project.

## Trimmed from the animation

Whole lines only; apart from the rename edit described above, nothing is reworded. Long lines are soft-wrapped at 92 columns, and Claude's markdown
emphasis markers (`*`, `**`) are not drawn.

- The agent's second Bash call (`cat` of the draft and the note) and its output.
- From `check-claims` output: the `notes: <path>` line, the table separator, and the two `OK` rows.
- The `EXIT=` lines the agent echoed.
- The `meta` record is not drawn.
