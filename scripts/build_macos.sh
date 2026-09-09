#!/bin/bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"
version="$(python3 -c "import sys; sys.path.insert(0, 'src'); from version import __version__; print(__version__)")"
arch -arm64 python3 -m PyInstaller --noconfirm --clean RollCall.spec
app="$root/dist/RollCall.app"
test -x "$app/Contents/MacOS/RollCall"
asset="$root/dist/RollCall-${version}-macOS-arm64.zip"
rm -f "$asset"
file "$app/Contents/MacOS/RollCall"
codesign --force --deep --sign - "$app"
codesign --verify --deep --strict --verbose=2 "$app"
ditto -c -k --sequesterRsrc --keepParent "$app" "$asset"
shasum -a 256 "$asset"
