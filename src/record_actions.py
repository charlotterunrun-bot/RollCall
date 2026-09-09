"""Shared validated transaction for importing an existing record workbook."""

from __future__ import annotations

from pathlib import Path

import excel_io
import paths
import storage
from errors import AppError


def import_record(source, target, source_data, *, confirm=None):
    """Import a prevalidated source snapshot into target atomically.

    ``confirm`` is a UI callback used only when an existing target would be
    replaced. Returning ``None`` means cancellation. An exact same-source
    import returns the already validated source snapshot as a successful
    no-copy result. The returned data is the candidate parsed during the transaction,
    rebound to the committed target and fingerprint; no post-commit reload is
    performed.
    """
    source = Path(source)
    target = Path(target)
    try:
        if source.resolve() == target.resolve():
            source_data.source_path = target
            return source_data
        expected = storage.fingerprint(target)
        if expected is not None and confirm is not None and not confirm():
            return None
        raw = source.read_bytes()
    except AppError:
        raise
    except OSError as exc:
        raise AppError("storage_read_failed", path=str(source)) from exc

    # Capture imported legacy bytes before replacing the destination.  The
    # source file itself is never modified.
    paths.ensure_upgrade_snapshot(target, source_path=source)
    candidate = {}

    def writer(temp):
        temp.write_bytes(raw)

    def validator(temp):
        candidate["data"] = excel_io.load_record(temp, sheet_name=source_data.sheet_name)

    committed = storage.atomic_write(
        target, writer, validator,
        expected_fingerprint=expected, backup_kind="manual",
    )
    data = candidate["data"]
    data.source_path = target
    data.fingerprint = committed
    return data
