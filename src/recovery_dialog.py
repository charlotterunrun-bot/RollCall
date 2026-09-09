"""Actionable startup and backup recovery dialogs."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
    QInputDialog,
)

import excel_io
import storage
from errors import AppError


ERROR_TEXT = {
    "storage_source_missing": "记录文件不存在，可以导入花名册。",
    "excel.invalid_file": "记录文件不是可读取的 Excel 文件。请重试、恢复备份或导入其他记录。",
    "excel.invalid_header": "记录文件缺少必需表头。请修复文件或恢复备份。",
    "excel.ambiguous_sheets": "记录文件有多个可用工作表，请明确选择工作表。",
    "storage_locked": "记录文件正在被另一个课堂点名实例使用。",
    "storage_lock_failed": "无法在数据目录建立写入锁，请检查目录权限。",
    "storage_conflict": "记录文件已被外部修改，请重新读取后再操作。",
    "config.invalid": "设置文件损坏。可以继续使用默认设置，并在设置中保存修复后的设置。",
    "config.read_failed": "设置文件无法读取，请检查权限。",
}


def error_text(error: BaseException) -> str:
    if isinstance(error, AppError):
        return ERROR_TEXT.get(error.code, f"操作失败（{error.code}）。请重试或选择恢复方式。")
    return f"操作失败：{error}"


class SheetChooser(QDialog):
    """Small explicit worksheet chooser used for ambiguous T3 parses."""

    def __init__(self, sheets, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择工作表")
        layout = QVBoxLayout(self)
        label = QLabel("请选择要使用的工作表：")
        layout.addWidget(label)
        self.list = QListWidget()
        self.list.addItems([str(s) for s in sheets])
        self.list.setCurrentRow(0)
        layout.addWidget(self.list)
        box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        layout.addWidget(box)

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
        self.setWindowTitle("记录恢复")
        self.setModal(True)
        layout = QVBoxLayout(self)
        title = QLabel("无法打开课堂记录")
        title.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(title)
        detail = QLabel(f"文件：{self.path}\n{error_text(error)}")
        detail.setTextFormat(Qt.TextFormat.PlainText)
        detail.setWordWrap(True)
        layout.addWidget(detail)
        self.backups = QListWidget()
        self.backups.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        try:
            self._backup_paths = storage.list_backups(self.path)
        except AppError:
            self._backup_paths = []
        for backup in self._backup_paths:
            self.backups.addItem(backup.name)
        layout.addWidget(QLabel("可用备份（选择后恢复）："))
        layout.addWidget(self.backups)
        buttons = QDialogButtonBox()
        self.retry_btn = buttons.addButton("重试", QDialogButtonBox.ButtonRole.AcceptRole)
        self.restore_btn = buttons.addButton("恢复选中备份", QDialogButtonBox.ButtonRole.ActionRole)
        self.import_btn = buttons.addButton("导入其他记录", QDialogButtonBox.ButtonRole.ActionRole)
        self.exit_btn = buttons.addButton("退出", QDialogButtonBox.ButtonRole.RejectRole)
        self.retry_btn.clicked.connect(self._retry)
        self.restore_btn.clicked.connect(self.restore_selected)
        self.import_btn.clicked.connect(self._import)
        self.exit_btn.clicked.connect(self._exit)
        layout.addWidget(buttons)

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
            QMessageBox.information(self, "选择备份", "请先选择一个备份。")
            return
        backup = self._backup_paths[row]
        answer = QMessageBox.question(
            self, "确认恢复", f"将用此备份替换当前记录：\n{backup.name}\n是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        candidate = {}

        def validate(candidate_path):
            try:
                candidate["data"] = excel_io.load_record(candidate_path)
            except AppError as exc:
                if exc.code != "excel.ambiguous_sheets":
                    raise
                sheet = choose_sheet(self, exc.params.get("sheets", []))
                if not sheet:
                    raise
                candidate["data"] = excel_io.load_record(candidate_path, sheet_name=sheet)

        try:
            committed = storage.restore_backup(self.path, backup, validate)
            data = candidate.get("data")
            if data is not None:
                data.source_path = self.path
                data.fingerprint = committed
            self.recovered.emit(data)
            self.accept()
        except AppError as exc:
            QMessageBox.critical(self, "恢复失败", error_text(exc))
