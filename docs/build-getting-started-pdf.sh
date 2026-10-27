#!/bin/sh
# Build the print PDF of docs/getting-started.md from the same source.
# Output: /tmp/getting-started-<shorthash>.pdf (no in-repo artefacts).
# Smart typography is OFF (-markdown-smart) so "--help" keeps two ASCII hyphens.
set -eu
cd "$(dirname "$0")/.."
rev=$(git rev-parse --short HEAD)
# Repo URL is read from README.md (not hard-coded: leak-check allows the public handle only in docs).
repo=$(grep -o 'https://github\.com/[A-Za-z0-9._-]*/research-kit' README.md | head -n 1)
[ -n "$repo" ] || { echo "no repo URL found in README.md" >&2; exit 1; }
url="$repo/blob/main/docs/getting-started.md"
out="/tmp/getting-started-$rev.pdf"
pandoc -f markdown-smart docs/getting-started.md -o "$out" \
  --pdf-engine=xelatex \
  -V geometry:margin=2cm -V colorlinks=true -V monofont=DejaVuSansMono \
  -M title="Getting started with research-kit" \
  -M date="revision $rev - current version: $url"
echo "$out"
