#!/usr/bin/env python3
"""Lint plugin skills: every SKILL.md needs front matter with `name` (= folder name) and a
non-empty `description`, and every plugins/provenote/ path it mentions must exist.
Stdlib only. Usage: python3 scripts/lint-skills.py [repo-root]"""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent)
skills = sorted((root / "plugins/provenote/skills").glob("*/SKILL.md"))
FM = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)
PATH = re.compile(r"plugins/provenote/[\w./-]*[\w/-]")
errors = []
if not skills:
    errors.append("no skills found under plugins/provenote/skills/")
for f in skills:
    rel = f.relative_to(root).as_posix()
    text = f.read_text(encoding="utf-8")
    m = FM.match(text)
    if not m:
        errors.append(f"{rel}: no YAML front matter")
        continue
    meta = {}
    lines = m.group(1).splitlines()
    for i, line in enumerate(lines):
        k, sep, v = line.partition(":")
        if sep and not line.startswith((" ", "\t", "#")):
            v = v.strip()
            if re.fullmatch(r"[>|][+-]?\d*\s*(#.*)?", v):  # block scalar: value is its indented body
                body = []
                for nxt in lines[i + 1:]:
                    if nxt.strip() and not nxt.startswith((" ", "\t")):
                        break
                    body.append(nxt.strip())
                v = " ".join(b for b in body if b)
            meta[k.strip()] = v.strip("'\"")
    if not meta.get("name"):
        errors.append(f"{rel}: empty or missing name")
    elif meta["name"] != f.parent.name:
        errors.append(f"{rel}: name {meta['name']!r} != folder {f.parent.name!r}")
    if not meta.get("description"):
        errors.append(f"{rel}: empty or missing description")
    for p in sorted(set(PATH.findall(text))):
        if not (root / p).exists():
            errors.append(f"{rel}: mentioned path does not exist: {p}")
for e in errors:
    print(f"FAIL {e}")
print(f"lint-skills: {len(skills)} skills, {len(errors)} problem(s)")
sys.exit(1 if errors else 0)
