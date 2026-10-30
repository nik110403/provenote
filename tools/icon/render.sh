#!/usr/bin/env bash
# Render assets/icon.svg -> plugins/provenote/.claude-plugin/icon.png (1024x1024, palette-optimised).
# Needs headless Chrome/Chromium and pngquant. Usage: tools/icon/render.sh
set -euo pipefail
cd "$(dirname "$0")/../.."
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
chrome=$(command -v google-chrome || command -v chromium || command -v chromium-browser)
printf '<html><body style="margin:0"><img src="file://%s/assets/icon.svg" width=1024 height=1024></body></html>' "$PWD" > "$tmp/i.html"
"$chrome" --headless --no-sandbox --disable-gpu --hide-scrollbars --window-size=1024,1024 --screenshot="$tmp/raw.png" "file://$tmp/i.html" >/dev/null 2>&1
pngquant --force --quality=90-100 --output plugins/provenote/.claude-plugin/icon.png "$tmp/raw.png"
