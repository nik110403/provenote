#!/usr/bin/env python3
"""Render the recorded demo transcript to animated SVGs (stdlib only).

  render.py extract <stream.jsonl> <transcript.jsonl> <prompt.txt>
                                                        reduce a `claude -p --output-format stream-json
                                                        --verbose` capture to prompt/command/result/text
                                                        records and sanitize paths
  render.py render  <transcript.jsonl> <assets-dir>     write demo-light.svg and demo-dark.svg

Every line drawn comes verbatim from transcript.jsonl (long lines are soft-wrapped, not cut).
Lines are dropped by the rules in SKIP below; see README.md for the list.
"""
import json
import re
import sys
import textwrap
from xml.sax.saxutils import escape

PUBLIC_ROOT = "~/provenote/tools/demo/fixture"
WIDTH_CH = 92          # wrap column
CH_W, LINE_H, FS = 8.4, 19, 14
PAD_X, TOP = 28, 52

# Output lines dropped from the animation (whole lines only).
SKIP = [
    re.compile(r"^notes: "),                 # path line
    re.compile(r"^\| \d+ \| \S+ \| OK \|"),  # rows that are fine
    re.compile(r"^\|---"),
    re.compile(r"^EXIT="),
    re.compile(r"^\s*$"),
]
FLAG = re.compile(r"FAIL|UNVERIFIED|UNCITED|isn't backed")

PALETTE = {
    "light": dict(bg="#faf7f2", panel="#f2ede4", ink="#1c1917", accent="#8c2f1b", stroke="#1c1917"),
    "dark": dict(bg="#0f0d0a", panel="#171410", ink="#f1ece2", accent="#e2855f", stroke="#f1ece2"),
}


def sanitize(s):
    s = re.sub(r"/[^\s]*?/tools/demo/fixture", PUBLIC_ROOT, s)
    s = re.sub(r"/h[o]me/[^/\s]+", "~", s)  # any user home dir
    return s


def extract(src, dst, prompt_file):
    out = [{"type": "prompt", "text": open(prompt_file).read().strip()}]
    for raw in open(src):
        d = json.loads(raw)
        if d["type"] == "system" and d.get("subtype") == "init":
            out.append({"type": "meta", "model": d.get("model"), "claude_code_version": d.get("claude_code_version")})
        if d["type"] not in ("assistant", "user"):
            continue
        content = d["message"]["content"]
        if isinstance(content, str):
            continue
        for c in content:
            if c["type"] == "tool_use":
                out.append({"type": "command", "text": c["input"].get("command", "")})
            elif c["type"] == "tool_result":
                t = c["content"]
                if not isinstance(t, str):
                    t = "\n".join(x.get("text", "") for x in t)
                out.append({"type": "result", "text": t})
            elif c["type"] == "text":
                out.append({"type": "text", "text": c["text"]})
    with open(dst, "w") as f:
        for r in out:
            f.write(sanitize(json.dumps(r, ensure_ascii=False)) + "\n")


def wrap(text, prefix="", indent="  "):
    return textwrap.wrap(prefix + text, WIDTH_CH, subsequent_indent=indent,
                         break_long_words=True, replace_whitespace=False) or [prefix]


def scene(records):
    """-> list of (kind, line); kind in prompt|out|flag|claude"""
    items, skip_result = [], False
    for r in records:
        if r["type"] == "prompt":
            items += [("ask", l) for l in wrap(r["text"], "> ", "  ")]
        elif r["type"] == "command" and r["text"].startswith("cat "):
            skip_result = True  # the agent re-reading files: dropped, with its output
        elif r["type"] == "command":
            items += [("prompt", l) for l in wrap(r["text"], "$ ", "  ")]
        elif r["type"] == "result" and skip_result:
            skip_result = False
        elif r["type"] == "result":
            for ln in r["text"].split("\n"):
                if any(p.search(ln) for p in SKIP):
                    continue
                kind = "flag" if FLAG.search(ln) else "out"
                items += [(kind, l) for l in wrap(ln, "", "    ")]
        elif r["type"] == "text":
            for ln in r["text"].split("\n"):
                if ln.strip():
                    items += [("claude", l) for l in wrap(ln.replace("**", "").replace("*", ""), "", "  ")]
    return items


def svg(items, theme):
    p = PALETTE[theme]
    mono = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
    W = int(PAD_X * 2 + WIDTH_CH * CH_W)
    H = TOP + LINE_H * len(items) + 28
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
             f'role="img" aria-label="Animated demo: a real Claude Code session verifying quotes and checking a draft">',
             f'<rect width="{W}" height="{H}" fill="{p["bg"]}"/>',
             f'<rect x="1" y="1" width="{W-2}" height="{H-2}" fill="{p["panel"]}" stroke="{p["stroke"]}" stroke-opacity="0.22"/>',
             f'<rect x="1" y="1" width="{W-2}" height="6" fill="{p["accent"]}"/>']
    t, defs, body = 0.8, [], []
    prev = None
    for i, (kind, line) in enumerate(items):
        y = TOP + i * LINE_H
        weight = 600 if kind in ("prompt", "ask", "flag") else 400
        fill = p["accent"] if kind in ("prompt", "ask", "flag") else p["ink"]
        op = ' fill-opacity="0.78"' if kind == "out" else ""
        txt = (f'<text x="{PAD_X}" y="{y}" font-family="{mono}" font-size="{FS}" font-weight="{weight}" '
               f'fill="{fill}"{op} xml:space="preserve"')
        if kind == "ask":  # the user prompt: one quick line-by-line reveal, 0.3 s per line
            body.append(txt + f' visibility="hidden">{escape(line)}'
                        f'<set attributeName="visibility" to="visible" begin="{t:.2f}s" fill="freeze"/></text>')
            t += 0.3
        elif kind == "prompt":
            # type the line out: clip width grows over the typing time
            dur = max(0.4, min(3.0, len(line) * 0.03))
            if prev not in ("prompt", "ask", None):
                t += 0.8
            n = len(line)  # typewriter: one clip step per character
            vals = ";".join(f"{k * CH_W:.1f}" for k in range(n + 2))
            defs.append(f'<clipPath id="c{i}"><rect x="{PAD_X-2}" y="{y-FS-2}" width="0" height="{LINE_H}">'
                        f'<animate attributeName="width" values="{vals}" dur="{dur:.2f}s" begin="{t:.2f}s" '
                        f'fill="freeze" calcMode="discrete"/></rect></clipPath>')
            body.append(txt + f' clip-path="url(#c{i})">{escape(line)}</text>')
            t += dur + (0.5 if i + 1 == len(items) or items[i + 1][0] != "prompt" else 0.1)
        else:
            body.append(txt + f' visibility="hidden">{escape(line)}'
                        f'<set attributeName="visibility" to="visible" begin="{t:.2f}s" fill="freeze"/></text>')
            t += 0.28 if kind != "claude" else 0.45
        prev = kind
    parts.append("<style>@media (prefers-reduced-motion: reduce){"
                 "text{visibility:visible !important;clip-path:none !important}}</style>")
    parts.append("<defs>" + "".join(defs) + "</defs>")
    parts += body
    parts.append("</svg>")
    return "\n".join(parts) + "\n", t


def main(argv):
    if len(argv) == 5 and argv[1] == "extract":
        extract(argv[2], argv[3], argv[4])
    elif len(argv) == 4 and argv[1] == "render":
        recs = [json.loads(l) for l in open(argv[2])]
        items = scene(recs)
        for theme in PALETTE:
            data, secs = svg(items, theme)
            open(f"{argv[3]}/demo-{theme}.svg", "w").write(data)
        print(f"{len(items)} lines, ~{secs:.0f}s")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
