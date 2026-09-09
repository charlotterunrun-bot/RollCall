"""Safe, crash-resistant persistence primitives for RollCall data files."""

from __future__ import annotations

import contextlib
import hashlib
import logging
import os
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator

from PySide6.QtCore import QLockFile

from errors import (
    AppError,
    STORAGE_BACKUP_FAILED,
    STORAGE_CONFLICT,
    STORAGE_INVALID_BACKUP,
    STORAGE_INVALID_BACKUP_KIND,
    STORAGE_LOCKED,
    STORAGE_LOCK_FAILED,
    STORAGE_READ_FAILED,
    STORAGE_REPLACE_FAILED,
    STORAGE_SOURCE_MISSING,
    STORAGE_VALIDATION_FAILED,
    STORAGE_WRITE_FAILED,
)


logger = logging.getLogger(__name__)
BACKUP_KINDS = frozenset({"auto", "upgrade", "manual", "pre_restore"})
AUTO_BACKUP_LIMIT = 50


def _as_path(path: Path) -> Path:
    return Path(path)


def _backup_dir(path: Path) -> Path:
    """Return the private sibling directory used for this file's backups."""
    return path.parent / ".rollcall-backups"


def backup_directory(path: Path) -> Path:
    """Return the backup directory, for recovery UI and diagnostics."""
    return _backup_dir(_as_path(path))


def fingerprint(path: Path) -> str | None:
    """Return a SHA-256 fingerprint, or ``None`` when *path* is absent."""
    path = _as_path(path)
    if not path.exists():
        return None
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except Exception as exc:
        raise AppError(STORAGE_READ_FAILED, path=str(path)) from exc
    return digest.hexdigest()


@contextlib.contextmanager
def transaction_lock(path: Path) -> Iterator[QLockFile]:
    """Acquire a nonblocking per-file QLockFile and release it on exit."""
    path = _as_path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        lock = QLockFile(str(path.parent / f"{path.name}.write.lock"))
        # QLockFile performs stale-lock detection.  Keep the timeout finite so
        # a terminated process does not permanently block future saves.
        lock.setStaleLockTime(60_000)
        if not lock.tryLock(0):
            error = lock.error()
            if error == QLockFile.LockError.LockFailedError:
                raise AppError(STORAGE_LOCKED, path=str(path))
            reason = getattr(error, "name", str(error))
            raise AppError(STORAGE_LOCK_FAILED, path=str(path), reason=reason)
    except AppError:
        raise
    except Exception as exc:
        raise AppError(STORAGE_LOCK_FAILED, path=str(path)) from exc

    try:
        yield lock
    finally:
        try:
            lock.unlock()
        except Exception:
            logger.warning("Could not release storage lock for %s", path, exc_info=True)


def _check_kind(kind: str) -> None:
    if kind not in BACKUP_KINDS:
        raise AppError(STORAGE_INVALID_BACKUP_KIND, kind=str(kind))


def _backup_pattern(path: Path) -> re.Pattern[str]:
    return re.compile(
        rf"^{re.escape(path.name)}\.\d{{8}}T\d{{12}}Z\.[0-9a-f]{{32}}\."
        rf"(?P<kind>auto|upgrade|manual|pre_restore)\.bak$"
    )


def list_backups(path: Path) -> list[Path]:
    """List application backups newest first; missing directories are empty."""
    path = _as_path(path)
    directory = _backup_dir(path)
    try:
        if not directory.is_dir():
            return []
        pattern = _backup_pattern(path)
        result = [
            entry
            for entry in directory.iterdir()
            if entry.is_file() and pattern.match(entry.name)
        ]
    except Exception as exc:
        raise AppError(STORAGE_READ_FAILED, path=str(directory)) from exc
    return sorted(result, key=lambda entry: entry.name, reverse=True)


def _new_backup_path(path: Path, kind: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return _backup_dir(path) / f"{path.name}.{timestamp}.{uuid.uuid4().hex}.{kind}.bak"


def _create_backup_locked(path: Path, kind: str) -> Path:
    _check_kind(kind)
    if not path.is_file():
        raise AppError(STORAGE_SOURCE_MISSING, path=str(path))
    directory = _backup_dir(path)
    destination = _new_backup_path(path, kind)
    try:
        directory.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
    except Exception as exc:
        try:
            destination.unlink(missing_ok=True)
        except Exception:
            logger.warning("Could not clean failed backup %s", destination, exc_info=True)
        raise AppError(STORAGE_BACKUP_FAILED, path=str(path), kind=kind) from exc
    return destination


def create_backup_copy(path: Path, source: Path, *, kind: str = "upgrade") -> Path:
    """Copy an arbitrary validated source into *path*'s permanent backup set."""
    path, source = _as_path(path), _as_path(source)
    _check_kind(kind)
    expected = fingerprint(source)
    if expected is None:
        raise AppError(STORAGE_SOURCE_MISSING, path=str(source))
    with transaction_lock(path):
        destination = _new_backup_path(path, kind)
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            _verify_backup_copy(destination, expected, source)
        except AppError:
            raise
        except Exception as exc:
            try:
                destination.unlink(missing_ok=True)
            except OSError:
                logger.warning("Could not clean failed backup %s", destination, exc_info=True)
            raise AppError(STORAGE_BACKUP_FAILED, path=str(source), kind=kind) from exc
    return destination


def _verify_backup_copy(backup: Path, expected: str | None, target: Path) -> None:
    """Ensure a raw backup still represents the bytes captured from target."""
    if fingerprint(backup) == expected:
        return
    try:
        backup.unlink(missing_ok=True)
    except Exception:
        logger.warning("Could not remove inconsistent backup %s", backup, exc_info=True)
    raise AppError(STORAGE_CONFLICT, path=str(target))


def create_backup(path: Path, *, kind: str = "manual") -> Path:
    """Create a uniquely named backup of *path* under the private backup dir."""
    path = _as_path(path)
    _check_kind(kind)
    with transaction_lock(path):
        return _create_backup_locked(path, kind)


def _prune_auto_backups(path: Path) -> None:
    pattern = _backup_pattern(path)
    auto = [
        entry
        for entry in list_backups(path)
        if (match := pattern.match(entry.name)) is not None
        and match.group("kind") == "auto"
    ]
    for entry in auto[AUTO_BACKUP_LIMIT:]:
        entry.unlink()


def _check_expected(path: Path, expected_fingerprint: str | None) -> None:
    current = fingerprint(path)
    if current != expected_fingerprint:
        raise AppError(STORAGE_CONFLICT, path=str(path))


def _make_temp(path: Path) -> Path:
    try:
        descriptor, name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
        )
        os.close(descriptor)
        return Path(name)
    except Exception as exc:
        raise AppError(STORAGE_WRITE_FAILED, path=str(path)) from exc


def _run_writer(temp: Path, writer: Callable[[Path], None]) -> None:
    try:
        writer(temp)
        if not temp.is_file():
            raise OSError("writer did not create a file")
    except AppError:
        raise
    except Exception as exc:
        raise AppError(STORAGE_WRITE_FAILED, path=str(temp)) from exc


def _run_validator(temp: Path, validator: Callable[[Path], None]) -> None:
    try:
        validator(temp)
    except AppError:
        raise
    except Exception as exc:
        raise AppError(STORAGE_VALIDATION_FAILED, path=str(temp)) from exc


def _replace(temp: Path, path: Path) -> None:
    try:
        os.replace(temp, path)
    except Exception as exc:
        raise AppError(STORAGE_REPLACE_FAILED, path=str(path)) from exc


def atomic_write(
    path: Path,
    writer: Callable[[Path], None],
    validator: Callable[[Path], None],
    *,
    expected_fingerprint: str | None,
    backup_kind: str = "auto",
) -> str:
    """Write via a validated sibling temp file and atomically replace *path*."""
    path = _as_path(path)
    _check_kind(backup_kind)
    with transaction_lock(path):
        _check_expected(path, expected_fingerprint)
        if path.is_file():
            backup = _create_backup_locked(path, backup_kind)
            _verify_backup_copy(backup, expected_fingerprint, path)

        temp = _make_temp(path)
        try:
            _run_writer(temp, writer)
            _run_validator(temp, validator)
            candidate_fingerprint = fingerprint(temp)
            if candidate_fingerprint is None:
                raise AppError(STORAGE_READ_FAILED, path=str(temp))
            # The target may have appeared or changed while the writer and
            # validator ran.  This check is intentionally immediately before
            # os.replace to narrow the external-editor race window.
            _check_expected(path, expected_fingerprint)
            _replace(temp, path)
        finally:
            try:
                temp.unlink(missing_ok=True)
            except Exception:
                logger.warning("Could not clean temporary storage file %s", temp, exc_info=True)

        committed = candidate_fingerprint
        if backup_kind == "auto":
            try:
                _prune_auto_backups(path)
            except Exception:
                # The replacement is already committed.  Keep all backups and
                # expose only a warning so a cleanup problem cannot masquerade
                # as a failed attendance write.
                logger.warning("Backup cleanup warning for %s", path, exc_info=True)
        return committed


def _validate_backup(backup: Path, validator: Callable[[Path], None]) -> str:
    if not backup.is_file():
        raise AppError(STORAGE_INVALID_BACKUP, path=str(backup))
    try:
        validator(backup)
    except AppError:
        raise
    except Exception as exc:
        raise AppError(STORAGE_INVALID_BACKUP, path=str(backup)) from exc
    result = fingerprint(backup)
    if result is None:
        raise AppError(STORAGE_INVALID_BACKUP, path=str(backup))
    return result


def restore_backup(
    path: Path, backup: Path, validator: Callable[[Path], None]
) -> str:
    """Validate and restore a backup, retaining the current target first."""
    path = _as_path(path)
    backup = _as_path(backup)
    if path == backup:
        raise AppError(STORAGE_INVALID_BACKUP, path=str(backup))

    with transaction_lock(path):
        # Capture the destination state before validating/copying the source.
        # This also treats an initially missing destination as a real
        # expectation: a file appearing during restore must not be replaced.
        destination_fingerprint = fingerprint(path)
        source_fingerprint = _validate_backup(backup, validator)
        if path.is_file():
            pre_restore = _create_backup_locked(path, "pre_restore")
            _verify_backup_copy(pre_restore, destination_fingerprint, path)

        temp = _make_temp(path)
        try:
            try:
                shutil.copy2(backup, temp)
            except Exception as exc:
                raise AppError(STORAGE_WRITE_FAILED, path=str(temp)) from exc
            _run_validator(temp, validator)
            candidate_fingerprint = fingerprint(temp)
            if candidate_fingerprint is None:
                raise AppError(STORAGE_READ_FAILED, path=str(temp))
            if fingerprint(backup) != source_fingerprint:
                raise AppError(STORAGE_CONFLICT, path=str(backup))
            # The pre-restore copy is only a snapshot of the destination at
            # transaction time.  Check the live destination immediately
            # before replacement so an external edit remains intact.
            _check_expected(path, destination_fingerprint)
            _replace(temp, path)
        finally:
            try:
                temp.unlink(missing_ok=True)
            except Exception:
                logger.warning("Could not clean restore temp file %s", temp, exc_info=True)

        return candidate_fingerprint
