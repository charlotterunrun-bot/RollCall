#!/bin/bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"
arch -arm64 python3 -m PyInstaller --noconfirm --clean RollCall.spec
app="$root/dist/RollCall.app"
test -x "$app/Contents/MacOS/RollCall"
asset="$root/dist/RollCall-2.0.0-macOS-arm64.zip"
rm -f "$asset"
ditto -c -k --sequesterRsrc --keepParent "$app" "$asset"
file "$app/Contents/MacOS/RollCall"
codesign --display --verbose=2 "$app" || true
shasum -a 256 "$asset"
