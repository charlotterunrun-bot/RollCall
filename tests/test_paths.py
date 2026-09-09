import json
import os
import sys
from pathlib import Path

import pytest


def test_source_data_dir_is_record_subdirectory_of_app_dir(tmp_path, monkeypatch):
    import paths

    monkeypatch.setattr(paths, "app_dir", lambda: str(tmp_path))
    paths.clear_data_dir()
    assert paths.data_dir() == tmp_path / "RollCallRecord"
    assert Path(paths.record_path()) == tmp_path / "RollCallRecord" / "record.xlsx"
    assert Path(paths.config_path()) == tmp_path / "RollCallRecord" / "config.json"


def test_frozen_windows_data_dir_sits_beside_executable(tmp_path, monkeypatch):
    import paths

    monkeypatch.setattr(paths.sys, "frozen", True, raising=False)
    monkeypatch.setattr(paths.sys, "executable", str(tmp_path / "RollCall.exe"))
    monkeypatch.setattr(paths.sys, "platform", "win32")
    paths.clear_data_dir()
    assert paths.data_dir() == tmp_path / "RollCallRecord"


def test_frozen_macos_data_dir_uses_stable_product_identifier(tmp_path, monkeypatch):
    import paths

    monkeypatch.setattr(paths.sys, "frozen", True, raising=False)
    monkeypatch.setattr(paths.sys, "platform", "darwin")
    monkeypatch.setattr(paths.Path, "home", lambda: tmp_path)
    paths.clear_data_dir()
    assert paths.data_dir() == tmp_path / "Library" / "Application Support" / "RollCall" / "RollCallRecord"


def test_resource_path_resolves_locale_and_templates(tmp_path, monkeypatch):
    import paths

    monkeypatch.setattr(paths.sys, "frozen", False, raising=False)
    monkeypatch.setattr(paths, "app_dir", lambda: str(tmp_path))
    assert Path(paths.resource_path("src/locales/en_US.json")).is_file()
    assert Path(paths.resource_path("resources/template-en.xlsx")).is_file()


def test_explicit_data_dir_override_is_absolute_and_resettable(tmp_path):
    import paths

    paths.set_data_dir(tmp_path / "chosen")
    assert paths.data_dir() == (tmp_path / "chosen").resolve()
    paths.clear_data_dir()


def test_upgrade_snapshot_is_permanent_and_deduplicated(tmp_path):
    import paths

    record = tmp_path / "RollCallRecord" / "record.xlsx"
    record.parent.mkdir()
    record.write_bytes(b"legacy")
    first = paths.ensure_upgrade_snapshot(record)
    second = paths.ensure_upgrade_snapshot(record)
    assert first == second
    assert first.is_file()
    assert first.read_bytes() == b"legacy"
    marker = paths.upgrade_marker_path(record)
    payload = json.loads(marker.read_text(encoding="utf-8"))
    assert payload["records"][paths.fingerprint(record)] == first.name


def test_upgrade_snapshot_tracks_imported_source_fingerprint(tmp_path):
    import paths

    target = tmp_path / "target" / "record.xlsx"
    source = tmp_path / "source.xlsx"
    target.parent.mkdir()
    source.write_bytes(b"imported-legacy")
    snapshot = paths.ensure_upgrade_snapshot(target, source_path=source)
    assert snapshot.read_bytes() == source.read_bytes()
    assert paths.fingerprint(source) in json.loads(paths.upgrade_marker_path(target).read_text(encoding="utf-8"))["records"]


def test_upgrade_lineage_advances_after_commit_without_new_snapshot(tmp_path):
    import paths

    record = tmp_path / "record.xlsx"
    record.write_bytes(b"legacy")
    first = paths.ensure_upgrade_snapshot(record)
    old_digest = paths.fingerprint(record)
    record.write_bytes(b"v2-attendance")
    new_digest = paths.fingerprint(record)
    paths.mark_upgrade_commit(record, old_digest, new_digest)
    assert paths.ensure_upgrade_snapshot(record) == first
    assert len(list((tmp_path / ".rollcall-backups").glob("*.upgrade.bak"))) == 1


def test_real_attendance_restart_keeps_one_upgrade_snapshot(tmp_path):
    import excel_io
    import storage

    record = tmp_path / "record.xlsx"
    data = excel_io.create_record_from_namelist(
        [{"seq": "1", "no": "S1", "name": "One", "clazz": "A"},
         {"seq": "2", "no": "S2", "name": "Two", "clazz": "A"}],
        path=record,
    )
    first = excel_io.write_record("S1", "2026-09-09", "到", data=data)
    assert len([p for p in storage.list_backups(record) if ".upgrade.bak" in p.name]) == 1
    restarted = excel_io.load_record(record)
    excel_io.write_record("S2", "2026-09-09", "到", data=restarted)
    assert len([p for p in storage.list_backups(record) if ".upgrade.bak" in p.name]) == 1


def test_missing_or_corrupt_active_upgrade_snapshot_is_recreated(tmp_path):
    import excel_io
    import json
    import paths
    import storage

    record = tmp_path / "record.xlsx"
    data = excel_io.create_record_from_namelist([{"seq": "1", "no": "S1", "name": "One", "clazz": "A"}], path=record)
    excel_io.write_record("S1", "2026-09-09", "到", data=data)
    marker_path = paths.upgrade_marker_path(record)
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    snapshot = record.parent / ".rollcall-backups" / marker["active_snapshot"]
    snapshot.write_bytes(b"corrupt")
    restarted = excel_io.load_record(record)
    excel_io.write_record("S1", "2026-09-10", "到", data=restarted)
    repaired = json.loads(marker_path.read_text(encoding="utf-8"))
    repaired_snapshot = record.parent / ".rollcall-backups" / repaired["active_snapshot"]
    assert repaired_snapshot.is_file()
    assert paths.fingerprint(repaired_snapshot) == repaired["snapshot_fingerprint"]
    assert len([p for p in storage.list_backups(record) if ".upgrade.bak" in p.name]) == 2


def test_distinct_legacy_import_gets_own_snapshot_and_preserves_source(tmp_path):
    import excel_io
    import storage
    from record_actions import import_record

    target = tmp_path / "target.xlsx"
    source = tmp_path / "source.xlsx"
    target_data = excel_io.create_record_from_namelist([{"seq": "1", "no": "T1", "name": "Target", "clazz": "A"}], path=target)
    excel_io.write_record("T1", "2026-09-09", "到", data=target_data)
    source_data = excel_io.create_record_from_namelist([{"seq": "1", "no": "S1", "name": "Source", "clazz": "A"}], path=source)
    original_source = source.read_bytes()
    imported = import_record(source, target, source_data, confirm=lambda: True)
    assert source.read_bytes() == original_source
    assert imported.students[0].id == "S1"
    upgrade = [p for p in storage.list_backups(target) if ".upgrade.bak" in p.name]
    assert len(upgrade) == 2


def test_unwritable_directory_selection_is_explicit_and_does_not_save_config(tmp_path, monkeypatch):
    import main
    import paths
    from errors import AppError

    selected = tmp_path / "chosen"
    calls = {"probe": 0, "save": 0}

    def probe():
        calls["probe"] += 1
        if calls["probe"] == 1:
            raise AppError("storage_data_dir_unwritable", path=str(tmp_path / "default"))
        return selected

    monkeypatch.setattr(main.paths, "ensure_data_dir", probe)
    monkeypatch.setattr(main.QFileDialog, "getExistingDirectory", lambda *args: str(selected))
    monkeypatch.setattr(main.i18n, "critical", lambda *args: None)
    monkeypatch.setattr(main.config, "save_settings", lambda *args, **kwargs: calls.__setitem__("save", calls["save"] + 1))
    assert main._prepare_data_dir() is True
    assert paths.data_dir() == selected.resolve()
    assert calls["save"] == 0


def test_second_instance_lock_rejects_without_config_rewrite(tmp_path):
    import json
    import main_window

    record = tmp_path / "record.xlsx"
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"language": "en_US"}), encoding="utf-8")
    first = main_window.acquire_session_lock(record)
    before = config.read_bytes()
    try:
        with pytest.raises(Exception):
            main_window.acquire_session_lock(record)
        assert config.read_bytes() == before
    finally:
        first.unlock()
