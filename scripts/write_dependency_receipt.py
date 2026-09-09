"""Write compact native build dependency/platform evidence."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("output", type=Path)
args = parser.parse_args()
payload = {
    "python": platform.python_version(),
    "platform": sys.platform,
    "arch": platform.machine(),
    "dependencies": {name: importlib.metadata.version(name) for name in ("PySide6", "PyInstaller", "openpyxl", "xlrd")},
}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, sort_keys=True))
