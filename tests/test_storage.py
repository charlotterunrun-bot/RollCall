import hashlib
import logging
from pathlib import Path

import pytest


def _valid(path: Path) -> None:
    if path.read_bytes().startswith(b"valid:") is False:
        raise ValueError("invalid payload")


def test_fingerprint_returns_sha256_and_none_for_missing(tmp_path):
    import storage

    path = tmp_path / "record.xlsx"
    path.write_bytes(b"record")

    assert storage.fingerprint(path) == hashlib.sha256(b"record").hexdigest()
    assert storage.fingerprint(tmp_path / "missing.xlsx") is None


def test_atomic_write_replaces_atomically_and_returns_fingerprint(tmp_path):
    import storage

    path = tmp_path / "record.xlsx"
    path.write_bytes(b"valid:old")
    before = storage.fingerprint(path)

    result = storage.atomic_write(
        path, lambda temp: temp.write_bytes(b"valid:new"), _valid,
        expected_fingerprint=before,
    )

    assert path.read_bytes() == b"valid:new"
    assert result == storage.fingerprint(path)
    assert result == hashlib.sha256(b"valid:new").hexdigest()
    assert len(storage.list_backups(path)) == 1


def test_failed_replace_preserves_original(tmp_path, monkeypatch):
    import storage
    from errors import AppError

    path = tmp_path / "record.xlsx"
    path.write_bytes(b"original")

    def fail_replace(*args):
        raise PermissionError("locked")

    monkeypatch.setattr(storage.os, "replace", fail_replace)
    with pytest.raises(AppError) as exc:
        storage.atomic_write(
            path, lambda p: p.write_bytes(b"new"), lambda p: None,
            expected_fingerprint=storage.fingerprint(path),
        )

    assert exc.value.code == "storage_replace_failed"
    assert isinstance(exc.value.__cause__, PermissionError)
    assert path.read_bytes() == b"original"


def test_backup_failure_preserves_original(tmp_path, monkeypatch):
    import storage
    from errors import AppError

    path = tmp_path / "record.xlsx"
    path.write_bytes(b"original")

    def fail_copy(*args, **kwargs):
        raise OSError("backup directory is read-only")

    monkeypatch.setattr(storage.shutil, "copy2", fail_copy)
    with pytest.raises(AppError) as exc:
        storage.atomic_write(
            path, lambda p: p.write_bytes(b"new"), lambda p: None,
            expected_fingerprint=storage.fingerprint(path),
        )

    assert exc.value.code == "storage_backup_failed"
    assert path.read_bytes() == b"original"


def test_validation_failure_preserves_original(tmp_path):
    import storage
    from errors import AppError

    path = tmp_path / "record.xlsx"
    path.write_bytes(b"valid:old")

    with pytest.raises(AppError) as exc:
        storage.atomic_write(
            path, lambda p: p.write_bytes(b"invalid"), _valid,
            expected_fingerprint=storage.fingerprint(path),
        )

    assert exc.value.code == "storage_validation_failed"
    assert path.read_bytes() == b"valid:old"


def test_fingerprint_conflict_is_checked_again_before_replace(tmp_path):
    import storage
    from errors import AppError

    path = tmp_path / "record.xlsx"
    path.write_bytes(b"valid:old")
    expected = storage.fingerprint(path)

    def writer(temp):
        temp.write_bytes(b"valid:new")
        path.write_bytes(b"valid:external")

    with pytest.raises(AppError) as exc:
        storage.atomic_write(path, writer, _valid, expected_fingerprint=expected)

    assert exc.value.code == "storage_conflict"
    assert path.read_bytes() == b"valid:external"


def test_new_file_detects_file_appearing_during_transaction(tmp_path):
    import storage
    from errors import AppError

    path = tmp_path / "new.xlsx"

    def writer(temp):
        temp.write_bytes(b"valid:new")
        path.write_bytes(b"valid:external")

    with pytest.raises(AppError) as exc:
        storage.atomic_write(path, writer, _valid, expected_fingerprint=None)

    assert exc.value.code == "storage_conflict"
    assert path.read_bytes() == b"valid:external"


def test_auto_backups_rotate_and_permanent_kinds_are_retained(tmp_path):
    import storage

    path = tmp_path / "record.xlsx"
    path.write_bytes(b"valid:0")
    permanent = storage.create_backup(path, kind="upgrade")
    assert permanent in storage.list_backups(path)

    for index in range(1, 56):
        storage.atomic_write(
            path, lambda temp, i=index: temp.write_bytes(f"valid:{i}".encode()),
            _valid, expected_fingerprint=storage.fingerprint(path),
        )

    backups = storage.list_backups(path)
    assert permanent in backups
    assert len([p for p in backups if ".auto." in p.name]) == 50
    assert len([p for p in backups if ".upgrade." in p.name]) == 1


def test_pruning_failure_after_replace_is_partial_success(tmp_path, monkeypatch, caplog):
    import storage

    path = tmp_path / "record.xlsx"
    path.write_bytes(b"valid:old")

    def fail_prune(*args, **kwargs):
        raise OSError("cannot remove old backup")

    monkeypatch.setattr(storage, "_prune_auto_backups", fail_prune)
    caplog.set_level(logging.WARNING, logger="storage")
    result = storage.atomic_write(
        path, lambda temp: temp.write_bytes(b"valid:new"), _valid,
        expected_fingerprint=storage.fingerprint(path),
    )

    assert path.read_bytes() == b"valid:new"
    assert result == storage.fingerprint(path)
    assert "cleanup" in caplog.text.lower()


def test_restore_rejects_invalid_backup_and_keeps_original(tmp_path):
    import storage
    from errors import AppError

    path = tmp_path / "record.xlsx"
    path.write_bytes(b"valid:old")
    bad = tmp_path / "record.xlsx.bad.bak"
    bad.write_bytes(b"invalid")

    with pytest.raises(AppError) as exc:
        storage.restore_backup(path, bad, _valid)

    assert exc.value.code == "storage_invalid_backup"
    assert path.read_bytes() == b"valid:old"
    assert not [p for p in storage.list_backups(path) if ".pre_restore." in p.name]


def test_restore_keeps_pre_restore_copy_of_original(tmp_path):
    import storage

    path = tmp_path / "record.xlsx"
    path.write_bytes(b"valid:old")
    backup = storage.create_backup(path, kind="manual")
    path.write_bytes(b"valid:current")

    result = storage.restore_backup(path, backup, _valid)

    assert path.read_bytes() == b"valid:old"
    assert result == storage.fingerprint(path)
    pre_restore = [p for p in storage.list_backups(path) if ".pre_restore." in p.name]
    assert len(pre_restore) == 1
    assert pre_restore[0].read_bytes() == b"valid:current"


def test_transaction_lock_is_nonblocking_and_released(tmp_path):
    import storage
    from errors import AppError

    path = tmp_path / "record.xlsx"
    with storage.transaction_lock(path):
        with pytest.raises(AppError) as exc:
            with storage.transaction_lock(path):
                pass
        assert exc.value.code == "storage_locked"

    with storage.transaction_lock(path):
        pass


def test_restore_rejects_destination_change_before_replace(tmp_path):
    import storage
    from errors import AppError

    path = tmp_path / "record.xlsx"
    path.write_bytes(b"valid:old")
    backup = storage.create_backup(path, kind="manual")
    path.write_bytes(b"valid:current")

    def validator(candidate):
        _valid(candidate)
        if candidate.name.endswith(".tmp"):
            path.write_bytes(b"valid:external")

    with pytest.raises(AppError) as exc:
        storage.restore_backup(path, backup, validator)

    assert exc.value.code == "storage_conflict"
    assert path.read_bytes() == b"valid:external"
    pre_restore = [p for p in storage.list_backups(path) if ".pre_restore." in p.name]
    assert len(pre_restore) == 1
    assert pre_restore[0].read_bytes() == b"valid:current"


def test_restore_rejects_destination_appearing_before_replace(tmp_path):
    import storage
    from errors import AppError

    path = tmp_path / "record.xlsx"
    backup_source = tmp_path / "source.xlsx"
    backup_source.write_bytes(b"valid:restore")

    def validator(candidate):
        _valid(candidate)
        if candidate.name.endswith(".tmp"):
            path.write_bytes(b"valid:external")

    with pytest.raises(AppError) as exc:
        storage.restore_backup(path, backup_source, validator)

    assert exc.value.code == "storage_conflict"
    assert path.read_bytes() == b"valid:external"
    pre_restore = [p for p in storage.list_backups(path) if ".pre_restore." in p.name]
    assert pre_restore == []


def test_atomic_write_returns_known_hash_when_target_read_fails_after_replace(
    tmp_path, monkeypatch
):
    import storage

    path = tmp_path / "record.xlsx"
    path.write_bytes(b"valid:old")
    expected = storage.fingerprint(path)
    original_fingerprint = storage.fingerprint

    def fail_new_target_read(candidate):
        if candidate == path and path.read_bytes() == b"valid:new":
            raise OSError("target was locked after replacement")
        return original_fingerprint(candidate)

    monkeypatch.setattr(storage, "fingerprint", fail_new_target_read)
    result = storage.atomic_write(
        path, lambda temp: temp.write_bytes(b"valid:new"), _valid,
        expected_fingerprint=expected,
    )

    assert result == hashlib.sha256(b"valid:new").hexdigest()
    assert path.read_bytes() == b"valid:new"


def test_restore_returns_committed_hash_if_target_changes_after_replace(
    tmp_path, monkeypatch
):
    import storage

    path = tmp_path / "record.xlsx"
    path.write_bytes(b"valid:old")
    backup = storage.create_backup(path, kind="manual")
    original_replace = storage._replace

    def replace_then_external_edit(temp, target):
        original_replace(temp, target)
        target.write_bytes(b"valid:external")

    monkeypatch.setattr(storage, "_replace", replace_then_external_edit)
    result = storage.restore_backup(path, backup, _valid)

    assert result == hashlib.sha256(b"valid:old").hexdigest()
    assert path.read_bytes() == b"valid:external"


def test_restore_rejects_inconsistent_pre_restore_copy(tmp_path, monkeypatch):
    import storage
    from errors import AppError

    path = tmp_path / "record.xlsx"
    path.write_bytes(b"valid:old")
    source = storage.create_backup(path, kind="manual")
    path.write_bytes(b"valid:current")
    original_copy = storage.shutil.copy2

    def corrupt_pre_restore(src, destination, *args, **kwargs):
        result = original_copy(src, destination, *args, **kwargs)
        if ".pre_restore." in Path(destination).name:
            Path(destination).write_bytes(b"valid:corrupt")
        return result

    monkeypatch.setattr(storage.shutil, "copy2", corrupt_pre_restore)
    with pytest.raises(AppError) as exc:
        storage.restore_backup(path, source, _valid)

    assert exc.value.code == "storage_conflict"
    assert path.read_bytes() == b"valid:current"


def test_atomic_write_rejects_inconsistent_auto_backup(tmp_path, monkeypatch):
    import storage
    from errors import AppError

    path = tmp_path / "record.xlsx"
    path.write_bytes(b"valid:old")
    original_copy = storage.shutil.copy2

    def corrupt_auto(src, destination, *args, **kwargs):
        result = original_copy(src, destination, *args, **kwargs)
        if ".auto." in Path(destination).name:
            Path(destination).write_bytes(b"valid:corrupt")
        return result

    monkeypatch.setattr(storage.shutil, "copy2", corrupt_auto)
    with pytest.raises(AppError) as exc:
        storage.atomic_write(
            path, lambda temp: temp.write_bytes(b"valid:new"), _valid,
            expected_fingerprint=storage.fingerprint(path),
        )

    assert exc.value.code == "storage_conflict"
    assert path.read_bytes() == b"valid:old"


def test_pruning_parses_backup_kind_for_auto_in_target_name(tmp_path):
    import storage

    path = tmp_path / "record.auto.xlsx"
    path.write_bytes(b"valid:0")
    permanent = storage.create_backup(path, kind="upgrade")

    for index in range(1, 56):
        storage.atomic_write(
            path, lambda temp, i=index: temp.write_bytes(f"valid:{i}".encode()),
            _valid, expected_fingerprint=storage.fingerprint(path),
        )

    backups = storage.list_backups(path)
    assert permanent in backups
    assert ".upgrade." in permanent.name
    assert len([p for p in backups if p.name.endswith(".auto.bak")]) == 50


def test_lock_permission_failure_is_not_reported_as_contention(tmp_path, monkeypatch):
    import storage
    from errors import AppError
    from PySide6.QtCore import QLockFile

    class PermissionDeniedLock:
        def __init__(self, path):
            self.path = path

        def setStaleLockTime(self, timeout):
            pass

        def tryLock(self, timeout):
            return False

        def error(self):
            return QLockFile.LockError.PermissionError

    monkeypatch.setattr(storage, "QLockFile", PermissionDeniedLock)
    with pytest.raises(AppError) as exc:
        with storage.transaction_lock(tmp_path / "record.xlsx"):
            pass

    assert exc.value.code == "storage_lock_failed"
