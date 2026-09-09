"""Actionable startup and backup recovery dialogs."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QListWidget, QVBoxLayout, QMessageBox

import excel_io
import i18n
import paths
import storage
from errors import AppError


def error_text(error: BaseException) -> str:
    return i18n.error_text(error)


class SheetChooser(QDialog):
    """Small explicit worksheet chooser used for ambiguous T3 parses."""

    def __init__(self, sheets, parent=None):
        super().__init__(parent)
        self._sheets = [str(s) for s in sheets]
        layout = QVBoxLayout(self)
        self.label = QLabel()
        layout.addWidget(self.label)
        self.list = QListWidget()
        self.list.addItems(self._sheets)
        self.list.setCurrentRow(0)
        layout.addWidget(self.list)
        self.box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.box.accepted.connect(self.accept)
        self.box.rejected.connect(self.reject)
        layout.addWidget(self.box)
        self.retranslate_ui()

    def retranslate_ui(self):
        self.setWindowTitle(i18n.tr("dialog.choose_sheet"))
        self.label.setText(i18n.tr("dialog.choose_sheet_hint"))
        self.box.button(QDialogButtonBox.StandardButton.Ok).setText(i18n.tr("button.ok"))
        self.box.button(QDialogButtonBox.StandardButton.Cancel).setText(i18n.tr("button.cancel"))

    @property
    def selected(self):
        item = self.list.currentItem()
        return item.text() if item else None


def choose_sheet(parent, sheets):
    dialog = SheetChooser(sheets, parent)
    return dialog.selected if dialog.exec() == QDialog.DialogCode.Accepted else None


class RecoveryDialog(QDialog):
    retry_requested = Signal()
    import_requested = Signal()
    exit_requested = Signal()
    recovered = Signal(object)

    def __init__(self, path, error, parent=None):
        super().__init__(parent)
        self.path = Path(path)
        self.error = error
        self.setModal(True)
        layout = QVBoxLayout(self)
        self.title_label = QLabel()
        self.title_label.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.title_label)
        self.detail = QLabel()
        self.detail.setTextFormat(Qt.TextFormat.PlainText)
        self.detail.setWordWrap(True)
        layout.addWidget(self.detail)
        self.backups = QListWidget()
        self.backups.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        try:
            self._backup_paths = storage.list_backups(self.path)
        except AppError:
            self._backup_paths = []
        for backup in self._backup_paths:
            self.backups.addItem(backup.name)
        self.backups_label = QLabel()
        layout.addWidget(self.backups_label)
        layout.addWidget(self.backups)
        buttons = QDialogButtonBox()
        self.retry_btn = buttons.addButton(" ", QDialogButtonBox.ButtonRole.AcceptRole)
        self.restore_btn = buttons.addButton(" ", QDialogButtonBox.ButtonRole.ActionRole)
        self.import_btn = buttons.addButton(" ", QDialogButtonBox.ButtonRole.ActionRole)
        self.exit_btn = buttons.addButton(" ", QDialogButtonBox.ButtonRole.RejectRole)
        self.retry_btn.clicked.connect(self._retry)
        self.restore_btn.clicked.connect(self.restore_selected)
        self.import_btn.clicked.connect(self._import)
        self.exit_btn.clicked.connect(self._exit)
        layout.addWidget(buttons)
        self.retranslate_ui()

    def retranslate_ui(self):
        self.setWindowTitle(i18n.tr("dialog.recovery"))
        self.title_label.setText(i18n.tr("dialog.recovery_title"))
        self.detail.setText(f"{i18n.tr('record.file')}: {self.path}\n{error_text(self.error)}")
        self.backups_label.setText(i18n.tr("dialog.available_backups"))
        self.retry_btn.setText(i18n.tr("button.retry"))
        self.restore_btn.setText(i18n.tr("button.restore"))
        self.import_btn.setText(i18n.tr("button.import"))
        self.exit_btn.setText(i18n.tr("button.exit"))

    def _retry(self):
        self.retry_requested.emit()

    def _import(self):
        self.import_requested.emit()

    def _exit(self):
        self.exit_requested.emit()
        self.reject()

    def restore_selected(self):
        row = self.backups.currentRow()
        if row < 0:
            i18n.information(self, i18n.tr("dialog.choose_backup"), i18n.tr("dialog.choose_backup_hint"))
            return
        backup = self._backup_paths[row]
        answer = i18n.question(
            self, i18n.tr("dialog.confirm"), i18n.tr("dialog.confirm_restore", name=backup.name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        candidate = {}
        selected_sheet = {"name": None}

        def validate(candidate_path):
            try:
                if selected_sheet["name"] is None:
                    candidate["data"] = excel_io.load_record(candidate_path)
                else:
                    candidate["data"] = excel_io.load_record(candidate_path, sheet_name=selected_sheet["name"])
            except AppError as exc:
                if exc.code != "excel.ambiguous_sheets":
                    raise
                sheet = choose_sheet(self, exc.params.get("sheets", []))
                if not sheet:
                    raise
                selected_sheet["name"] = sheet
                candidate["data"] = excel_io.load_record(candidate_path, sheet_name=sheet)

        try:
            # Protect the selected legacy bytes before restore replaces the
            # current record; this also covers restoring a different import.
            paths.ensure_upgrade_snapshot(self.path, source_path=backup)
            committed = storage.restore_backup(self.path, backup, validate)
            data = candidate.get("data")
            if data is not None:
                data.source_path = self.path
                data.fingerprint = committed
            self.recovered.emit(data)
            self.accept()
        except AppError as exc:
            i18n.critical(self, i18n.tr("dialog.restore_failed"), error_text(exc))
