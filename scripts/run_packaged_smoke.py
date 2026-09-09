"""Run the actual packaged executable against a fresh temporary directory."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()
    raw = tempfile.mkdtemp(prefix="rollcall-smoke-")
    data_dir = Path(raw)
    environment = os.environ.copy()
    environment.update({"QT_QPA_PLATFORM": "offscreen", "PYTHONIOENCODING": "utf-8"})
    options = {}
    if sys.platform == "win32":
        options["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    process = subprocess.Popen(
        [str(args.executable), "--smoke-test", "--data-dir", str(data_dir)],
        env=environment,
        **options,
    )
    try:
        completed_code = process.wait(timeout=args.timeout)
    except subprocess.TimeoutExpired:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=False, capture_output=True)
        else:
            process.kill()
        print(f"packaged smoke timed out; evidence directory preserved: {data_dir}")
        if (data_dir / "smoke-result.json").is_file():
            print((data_dir / "smoke-result.json").read_text(encoding="utf-8"))
        return 1
    try:
        report = data_dir / "smoke-result.json"
        if completed_code != 0 or not report.is_file():
            return completed_code or 1
        payload = json.loads(report.read_text(encoding="utf-8"))
        if payload.get("mode") != "packaged-offscreen" or not payload.get("record_reloaded"):
            return 1
        if payload.get("version") != "2.0.0" or not payload.get("frozen"):
            return 1
        if payload.get("attendance_count") != 2:
            return 1
        if not (data_dir / "record.xlsx").is_file():
            return 1
        return 0
    finally:
        shutil.rmtree(raw, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
