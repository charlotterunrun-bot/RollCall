"""Stable application errors shared by the UI and persistence layers."""


class AppError(Exception):
    """An expected, user-actionable failure.

    ``code`` is stable and suitable for translation lookup.  ``params`` only
    contains safe display values such as paths; the original exception is
    retained through normal exception chaining (``__cause__``).
    """

    def __init__(self, code: str, **params):
        self.code = code
        self.params = dict(params)
        super().__init__(code)


STORAGE_LOCKED = "storage_locked"
STORAGE_LOCK_FAILED = "storage_lock_failed"
STORAGE_CONFLICT = "storage_conflict"
STORAGE_BACKUP_FAILED = "storage_backup_failed"
STORAGE_SOURCE_MISSING = "storage_source_missing"
STORAGE_WRITE_FAILED = "storage_write_failed"
STORAGE_VALIDATION_FAILED = "storage_validation_failed"
STORAGE_REPLACE_FAILED = "storage_replace_failed"
STORAGE_READ_FAILED = "storage_read_failed"
STORAGE_INVALID_BACKUP = "storage_invalid_backup"
STORAGE_INVALID_BACKUP_KIND = "storage_invalid_backup_kind"

