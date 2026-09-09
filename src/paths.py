"""Stable platform paths and durable upgrade protection for RollCall."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

TEMPLATE_NAME = "namelist模板.xls"
PRODUCT_NAME = "RollCall"
RECORD_DIR_NAME = "RollCallRecord"
_explicit_data_dir: Path | None = None


def app_dir() -> str:
    """Directory containing the executable, or the source launch directory."""
    if getattr(sys, "frozen", False):
        return str(Path(sys.executable).resolve().parent)
    return os.getcwd()


def default_data_dir() -> Path:
    if getattr(sys, "frozen", False) and sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / PRODUCT_NAME / RECORD_DIR_NAME
    return Path(app_dir()) / RECORD_DIR_NAME


def set_data_dir(path: str | os.PathLike[str]) -> Path:
    global _explicit_data_dir
    _explicit_data_dir = Path(path).expanduser().resolve()
    return _explicit_data_dir


def clear_data_dir() -> None:
    global _explicit_data_dir
    _explicit_data_dir = None


def data_dir() -> Path:
    """Return the selected data root, independent of translated UI text."""
    return _explicit_data_dir if _explicit_data_dir is not None else default_data_dir()


def ensure_data_dir(path: str | os.PathLike[str] | None = None) -> Path:
    """Create and probe a data directory, raising a structured app error."""
    target = (Path(path) if path is not None else data_dir()).expanduser().resolve()
    try:
        target.mkdir(parents=True, exist_ok=True)
        descriptor, name = tempfile.mkstemp(prefix=".rollcall-write-", dir=target)
        os.close(descriptor)
        Path(name).unlink()
    except Exception as exc:
        from errors import AppError
        raise AppError("storage_data_dir_unwritable", path=str(target)) from exc
    return target


def record_dir() -> str:
    return str(data_dir())


def record_path() -> str:
    return str(data_dir() / "record.xlsx")


def config_path() -> str:
    return str(data_dir() / "config.json")


def resource_path(name: str) -> str:
    """Resolve a bundled resource in a frozen app or source checkout."""
    if getattr(sys, "frozen", False):
        return str(Path(sys._MEIPASS) / name)  # noqa: SLF001
    return str(Path(__file__).resolve().parents[1] / name)


def fingerprint(path: str | os.PathLike[str]) -> str | None:
    from storage import fingerprint as storage_fingerprint
    return storage_fingerprint(Path(path))


def upgrade_marker_path(record_path: str | os.PathLike[str] | None = None) -> Path:
    target = Path(record_path or globals()["record_path"]())
    return target.parent / ".rollcall-upgrade-v2.json"


def _write_marker(marker: Path, payload: dict) -> None:
    marker.parent.mkdir(parents=True, exist_ok=True)
    temp = marker.with_name(f".{marker.name}.{uuid.uuid4().hex}.tmp")
    try:
        temp.write_bytes(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
        os.replace(temp, marker)
    finally:
        temp.unlink(missing_ok=True)


def ensure_upgrade_snapshot(record_path: str | os.PathLike[str], *, source_path: str | os.PathLike[str] | None = None) -> Path:
    """Capture a permanent pre-v2 copy once for each protected byte stream."""
    target = Path(record_path)
    source = Path(source_path) if source_path is not None else target
    digest = fingerprint(source)
    if digest is None:
        from errors import AppError
        raise AppError("storage_source_missing", path=str(source))
    marker = upgrade_marker_path(target)
    temp = None
    try:
        payload = json.loads(marker.read_text(encoding="utf-8")) if marker.is_file() else {}
        records = payload.get("records", {}) if isinstance(payload, dict) else {}
        existing = records.get(digest)
        active_snapshot = payload.get("active_snapshot")
        if payload.get("active_fingerprint") == digest and active_snapshot:
            snapshot = marker.parent / ".rollcall-backups" / active_snapshot
            expected_snapshot = payload.get("snapshot_fingerprint", digest)
            if snapshot.is_file() and fingerprint(snapshot) == expected_snapshot:
                return snapshot
        if existing:
            snapshot = marker.parent / ".rollcall-backups" / existing
            if snapshot.is_file() and fingerprint(snapshot) == digest:
                if payload.get("active_fingerprint") != digest:
                    payload = {"version": 2, "active_fingerprint": digest, "active_snapshot": snapshot.name, "snapshot_fingerprint": digest, "records": records}
                    _write_marker(marker, payload)
                return snapshot
        from storage import create_backup_copy
        snapshot = create_backup_copy(target, source, kind="upgrade")
        if fingerprint(snapshot) != digest:
            raise OSError("upgrade snapshot changed while copying")
        records[digest] = snapshot.name
        _write_marker(marker, {"version": 2, "active_fingerprint": digest, "active_snapshot": snapshot.name, "snapshot_fingerprint": digest, "records": records})
        return snapshot
    except Exception as exc:
        if temp is not None:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass
        from errors import AppError
        if isinstance(exc, AppError):
            raise
        raise AppError("storage_upgrade_snapshot_failed", path=str(source)) from exc


def mark_upgrade_commit(record_path: str | os.PathLike[str], previous_fingerprint: str, committed_fingerprint: str) -> None:
    """Advance the protected lineage after a successful record replacement."""
    marker = upgrade_marker_path(record_path)
    if not marker.is_file():
        return
    payload = json.loads(marker.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("active_fingerprint") != previous_fingerprint:
        return
    payload["active_fingerprint"] = committed_fingerprint
    _write_marker(marker, payload)
