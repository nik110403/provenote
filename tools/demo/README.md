# README demo (assets/demo-light.svg, assets/demo-dark.svg)

An animated SVG (about 18 s, plays once) built from one real Claude Code run. Nothing in it is typed
by hand: every line drawn comes from `transcript.jsonl`.

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
  --no-session-persistence --allowedTools "Bash" --max-budget-usd 1 "<prompt, first record of transcript.jsonl>"
```

The plugin was loaded with `--plugin-dir`, so its `bin/` tools were on PATH. The run cost about 0.31 USD.

## Files

- `transcript.jsonl`: the capture reduced by `render.py extract` to prompt, `meta`, Bash commands, tool
  results and Claude's text. Dropped from the raw stream: hook output, thinking blocks, rate-limit and
  token events. Paths are sanitized to `~/research-kit/tools/demo/fixture`.
- `render.py`: stdlib-only; the prompt appears line by line (0.3 s each), commands are typed, output reveals line by line. `python3 -I render.py render transcript.jsonl ../../assets` writes both SVGs.
- `fixture/`: the demo project.

## Trimmed from the animation

Whole lines only; nothing is reworded. Long lines are soft-wrapped at 92 columns, and Claude's markdown
emphasis markers (`*`, `**`) are not drawn.

- The agent's second Bash call (`cat` of the draft and the note) and its output.
- From `check-claims` output: the `notes: <path>` line, the table separator, and the two `OK` rows.
- The `EXIT=` lines the agent echoed.
- The `meta` record is not drawn.
