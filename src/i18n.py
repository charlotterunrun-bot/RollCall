"""Centralized, safe application translations."""

from __future__ import annotations

import json
import locale
import re
from pathlib import Path

from PySide6.QtCore import QLocale, Qt
from PySide6.QtWidgets import QMessageBox

import paths
from errors import AppError

SUPPORTED_LANGUAGES = ("zh_CN", "en_US")
_language = "zh_CN"
_resources = {}
_PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def locale_path(language: str) -> str:
    language = language if language in SUPPORTED_LANGUAGES else "en_US"
    return paths.resource_path(f"src/locales/{language}.json")


def _load(language: str) -> dict:
    if language not in _resources:
        try:
            _resources[language] = json.loads(Path(locale_path(language)).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _resources[language] = {}
    return _resources[language]


def placeholders(text: str) -> set[str]:
    return {match.group(1) for match in _PLACEHOLDER.finditer(str(text))}


class _SafeParams(dict):
    def __missing__(self, key):
        return ""


def tr(key: str, **params) -> str:
    text = _load(_language).get(key, _load("en_US").get(key, key))
    try:
        return str(text).format_map(_SafeParams(params))
    except (ValueError, IndexError):
        return str(text)


def language() -> str:
    return _language


def set_language(value: str) -> None:
    global _language
    _language = value if value in SUPPORTED_LANGUAGES else "en_US"


def system_language() -> str:
    locale_name = QLocale.system().name().casefold()
    if locale_name.startswith("zh"):
        return "zh_CN"
    for ui_language in QLocale.system().uiLanguages():
        if str(ui_language).casefold().startswith(("zh", "zh-hans")):
            return "zh_CN"
    # Keep the locale module fallback for minimal/offscreen Qt builds.
    value = locale.getlocale()[0] or ""
    return "zh_CN" if value.casefold().startswith("zh") else "en_US"


def _message_box(icon, parent, title, text, buttons, default):
    box = QMessageBox(icon, title, text, QMessageBox.StandardButton.NoButton, parent)
    box.setTextFormat(Qt.TextFormat.PlainText)
    box.setStandardButtons(buttons)
    labels = {
        QMessageBox.StandardButton.Yes: "button.yes",
        QMessageBox.StandardButton.No: "button.no",
        QMessageBox.StandardButton.Ok: "button.ok",
        QMessageBox.StandardButton.Cancel: "button.cancel",
        QMessageBox.StandardButton.Retry: "button.retry",
        QMessageBox.StandardButton.Close: "button.close",
    }
    for standard, key in labels.items():
        button = box.button(standard)
        if button is not None and buttons & standard:
            button.setText(tr(key))
    box.setDefaultButton(default)
    return box.exec()


def information(parent, title, text):
    from PySide6.QtWidgets import QMessageBox
    return _message_box(QMessageBox.Icon.Information, parent, title, text, QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok)


def warning(parent, title, text):
    from PySide6.QtWidgets import QMessageBox
    return _message_box(QMessageBox.Icon.Warning, parent, title, text, QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok)


def critical(parent, title, text):
    from PySide6.QtWidgets import QMessageBox
    return _message_box(QMessageBox.Icon.Critical, parent, title, text, QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok)


def question(parent, title, text, buttons, default):
    return _message_box(QMessageBox.Icon.Question, parent, title, text, buttons, default)


def initialize() -> AppError | None:
    """Set system language, then adopt a persisted valid choice.

    The caller displays the returned config error after QApplication exists,
    before startup probes or recovery dialogs are created.
    """
    set_language(system_language())
    try:
        import config
        if Path(paths.config_path()).exists():
            persisted = config.load_language()
            if persisted is not None:
                set_language(persisted)
    except AppError as exc:
        return exc
    return None


def error_text(error: BaseException) -> str:
    if not isinstance(error, AppError):
        return tr("error.generic", reason=str(error))
    params = dict(error.params)
    field = params.get("field")
    if error.code == "config.invalid":
        params["field"] = f" (field: {field})" if field and language() == "en_US" else (f"（字段：{field}）" if field else "")
    if error.code == "excel.invalid_header":
        sheet = params.get("sheet")
        params["sheet"] = f" (worksheet: {sheet})" if sheet and language() == "en_US" else (f"（工作表：{sheet}）" if sheet else "")
    key = f"error.{error.code}"
    text = tr(key, **params) if key in _load(_language) or key in _load("en_US") else tr("error.unknown", code=error.code, **params)
    return text + _error_context(error.code, params)


def _error_context(code: str, params: dict) -> str:
    """Append only supplied actionable location/context fields."""
    fields = ("path", "sheet", "row", "column", "range", "reason")
    rendered = {
        "excel.invalid_header": {"sheet"}, "excel.sheet_not_found": {"sheet"},
        "excel.formula_key_field": {"row", "column"}, "excel.merged_key_field": {"range"},
        "excel.invalid_sequence": {"row", "column"}, "excel.invalid_student_id": {"row", "column"},
        "excel.empty_student_id": {"row"}, "excel.empty_student_name": {"row"},
        "excel.duplicate_student_id": {"row"}, "excel.student_id_precision": {"row", "column"},
        "storage_backup_failed": {"path"}, "storage_source_missing": {"path"},
        "storage_write_failed": {"path"}, "storage_validation_failed": {"path"},
        "storage_replace_failed": {"path"}, "storage_read_failed": {"path"},
        "storage_invalid_backup": {"path"}, "config.invalid": {"field"},
    }.get(code, set())
    labels = {
        "path": "path" if language() == "en_US" else "路径",
        "sheet": "worksheet" if language() == "en_US" else "工作表",
        "row": "row" if language() == "en_US" else "行",
        "column": "column" if language() == "en_US" else "列",
        "range": "range" if language() == "en_US" else "范围",
        "reason": "reason" if language() == "en_US" else "原因",
    }
    parts = [f"{labels[field]}={params[field]}" for field in fields if field in params and params[field] not in (None, "") and field not in rendered]
    if not parts:
        return ""
    return (" [" + "; ".join(parts) + "]") if language() == "en_US" else ("（" + "；".join(parts) + "）")
