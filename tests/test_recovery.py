import json
from pathlib import Path

import pytest


@pytest.fixture
def qapp():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


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


def test_restore_uses_one_sheet_choice_for_all_validator_calls(tmp_path, monkeypatch, qapp):
    from PySide6.QtWidgets import QMessageBox
    from errors import AppError
    from excel_io import RollCallData
    import recovery_dialog
    import storage

    target = tmp_path / "record.xlsx"
    backup = tmp_path / "record.xlsx.20260909T000000000000Z.0123456789abcdef0123456789abcdef.manual.bak"
    backup.write_bytes(b"synthetic")
    monkeypatch.setattr(storage, "list_backups", lambda path: [backup])
    monkeypatch.setattr(recovery_dialog.i18n, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(recovery_dialog.i18n, "critical", lambda *a, **k: None)
    choices = []
    monkeypatch.setattr(recovery_dialog, "choose_sheet", lambda *a, **k: choices.append("record") or "record")
    calls = []

    def load(path, **kwargs):
        calls.append(kwargs.get("sheet_name"))
        if len(calls) == 1:
            raise AppError("excel.ambiguous_sheets", sheets=["record", "backup"])
        return RollCallData([], {}, source_path=path, sheet_name=kwargs.get("sheet_name"))

    monkeypatch.setattr(recovery_dialog.excel_io, "load_record", load)
    monkeypatch.setattr(storage, "restore_backup", lambda path, source, validator: (validator(source), validator(source), "hash")[2])
    dialog = recovery_dialog.RecoveryDialog(target, AppError("excel.invalid_file", path=str(target)))
    dialog.recovered.connect(lambda data: setattr(dialog, "result_data", data))
    dialog.backups.setCurrentRow(0)
    dialog.restore_selected()
    assert choices == ["record"]
    assert calls == [None, "record", "record"]
    assert dialog.result_data.sheet_name == "record"
    dialog.close()


def test_same_source_import_adopts_explicit_sheet_without_writing(tmp_path, monkeypatch):
    from excel_io import RollCallData
    from record_actions import import_record
    import storage

    target = tmp_path / "record.xlsx"
    target.write_bytes(b"unchanged")
    data = RollCallData([], {}, source_path=target, sheet_name="selected")
    before = target.read_bytes()
    monkeypatch.setattr(storage, "atomic_write", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not write")))
    result = import_record(target, target, data, confirm=lambda: (_ for _ in ()).throw(AssertionError("must not confirm")))
    assert result is data
    assert result.sheet_name == "selected"
    assert target.read_bytes() == before
