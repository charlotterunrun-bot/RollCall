import json
import os
import subprocess
from pathlib import Path

import pytest


def test_smoke_runner_requires_actual_packaged_executable(tmp_path):
    executable = os.environ.get("ROLLCALL_SMOKE_EXECUTABLE")
    if not executable:
        pytest.skip("set ROLLCALL_SMOKE_EXECUTABLE to an actual built executable")
    path = Path(executable)
    assert path.is_file(), path
    data_dir = tmp_path / "smoke-data"
    data_dir.mkdir()
    environment = os.environ.copy()
    environment.update({"QT_QPA_PLATFORM": "offscreen", "PYTHONIOENCODING": "utf-8"})
    result = subprocess.run(
        [str(path), "--smoke-test", "--data-dir", str(data_dir)],
        timeout=90,
        check=False,
        env=environment,
    )
    assert result.returncode == 0
    report = data_dir / "smoke-result.json"
    assert report.is_file()
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["mode"] == "packaged-offscreen"
    assert payload["record_reloaded"] is True
    assert payload["languages"] == ["zh_CN", "en_US"]
    assert (data_dir / "record.xlsx").is_file()
