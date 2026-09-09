"""Run the actual packaged executable against a fresh temporary directory."""
from __future__ import annotations

import argparse
import json
import os
import signal
import shutil
import subprocess
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from version import __version__


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    raw = tempfile.mkdtemp(prefix="rollcall-smoke-")
    data_dir = Path(raw)
    environment = os.environ.copy()
    environment.update({"QT_QPA_PLATFORM": "offscreen", "PYTHONIOENCODING": "utf-8"})
    options = {}
    if sys.platform == "win32":
        options["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    else:
        options["start_new_session"] = True
    process = subprocess.Popen(
        [str(args.executable), "--smoke-test", "--data-dir", str(data_dir)],
        env=environment,
        **options,
    )
    def preserve_evidence():
        if args.output_dir is None:
            return
        destination = args.output_dir.expanduser().resolve()
        destination.mkdir(parents=True, exist_ok=True)
        run_destination = destination / "run"
        shutil.copytree(data_dir, run_destination, dirs_exist_ok=True)
        print(f"packaged smoke evidence: {run_destination}")
    def write_failure(reason):
        (data_dir / "smoke-runner-result.json").write_text(
            json.dumps({
                "status": "failed",
                "reason": reason,
                "returncode": process.returncode,
                "report_exists": (data_dir / "smoke-result.json").is_file(),
            }, indent=2), encoding="utf-8"
        )
    def terminate_and_reap():
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=False, capture_output=True)
        else:
            os.killpg(process.pid, signal.SIGKILL)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    try:
        completed_code = process.wait(timeout=args.timeout)
    except subprocess.TimeoutExpired:
        terminate_and_reap()
        write_failure("timeout")
        preserve_evidence()
        print(f"packaged smoke timed out; evidence directory preserved: {data_dir}")
        if (data_dir / "smoke-result.json").is_file():
            print((data_dir / "smoke-result.json").read_text(encoding="utf-8"))
        return 1
    try:
        report = data_dir / "smoke-result.json"
        if completed_code != 0 or not report.is_file():
            write_failure("process_failed_or_report_missing")
            preserve_evidence()
            return completed_code or 1
        try:
            payload = json.loads(report.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            write_failure("smoke_report_invalid_json")
            preserve_evidence()
            return 1
        if payload.get("mode") != "packaged-offscreen" or not payload.get("record_reloaded"):
            write_failure("smoke_report_incomplete")
            preserve_evidence()
            return 1
        if payload.get("version") != __version__ or not payload.get("frozen"):
            write_failure("version_or_frozen_mismatch")
            preserve_evidence()
            return 1
        expected_arches = {"darwin": {"arm64", "aarch64"}, "win32": {"x86_64", "amd64"}}
        accepted_arches = expected_arches.get(sys.platform)
        if accepted_arches is None or str(payload.get("arch", "")).casefold() not in accepted_arches or payload.get("pointer_bits") != 64:
            write_failure("platform_or_arch_mismatch")
            preserve_evidence()
            return 1
        if payload.get("attendance_count") != 2:
            write_failure("attendance_count_mismatch")
            preserve_evidence()
            return 1
        if payload.get("students") != ["SMOKE-1", "SMOKE-2"] or payload.get("statuses") != ["到", "到"]:
            write_failure("attendance_values_mismatch")
            preserve_evidence()
            return 1
        if not (data_dir / "record.xlsx").is_file():
            write_failure("record_missing")
            preserve_evidence()
            return 1
        preserve_evidence()
        return 0
    finally:
        shutil.rmtree(raw, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
