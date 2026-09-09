import json
from pathlib import Path

import pytest


def test_probe_record_distinguishes_missing_empty_and_ready(tmp_path, monkeypatch):
    import excel_io

    path = tmp_path / "record.xlsx"
    assert excel_io.probe_record(path) == "missing"

    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "record"
    ws.append(["序号", "学号", "姓名", "班级"])
    wb.save(path)
    wb.close()
    assert excel_io.probe_record(path) == "empty"

    path.write_bytes(b"not an excel file")
    with pytest.raises(Exception) as exc:
        excel_io.probe_record(path)
    assert getattr(exc.value, "code", None) == "excel.invalid_file"


def test_config_save_failure_keeps_existing_values_and_bytes(tmp_path, monkeypatch):
    import config
    import paths
    from errors import AppError

    Path(paths.record_dir()).mkdir()
    cfg = Path(paths.config_path())
    cfg.write_text("{broken", encoding="utf-8")
    before = cfg.read_bytes()
    monkeypatch.setattr(config.storage, "atomic_write", lambda *a, **k: (_ for _ in ()).throw(AppError("storage_replace_failed")))
    with pytest.raises(AppError) as exc:
        config.save_settings(strategy=config.STRATEGY_SEQ_COUNT)
    assert getattr(exc.value, "code", None) == "storage_replace_failed"
    assert cfg.read_bytes() == before


def test_config_save_uses_atomic_write_and_keeps_corrupt_bytes_as_backup(tmp_path):
    import config
    import paths
    import storage

    Path(paths.record_dir()).mkdir()
    cfg = Path(paths.config_path())
    cfg.write_text("{broken", encoding="utf-8")
    config.save_settings(strategy=config.STRATEGY_SEQ_COUNT)
    assert json.loads(cfg.read_text(encoding="utf-8"))["strategy"] == config.STRATEGY_SEQ_COUNT
    backups = storage.list_backups(cfg)
    assert backups
    assert any(p.read_bytes() == b"{broken" for p in backups)
