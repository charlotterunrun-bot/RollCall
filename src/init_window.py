"""First-run and empty-record initialization window."""

import shutil
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

import config
import excel_io
import i18n
import paths
import storage
from errors import AppError
from recovery_dialog import choose_sheet, error_text
from main_window import acquire_session_lock
from version import window_title


class InitWindow(QWidget):
    initialized = Signal()

    def __init__(self, *, target_path=None, session_lock=None, acquire_lock=False):
        super().__init__()
        self.setObjectName("root")
        self.resize(640, 480)
        self.setMinimumSize(560, 420)
        self.target_path = Path(target_path or paths.record_path())
        self._session_lock = session_lock
        if acquire_lock and session_lock is None:
            self._session_lock = acquire_session_lock(self.target_path)
        self._build()

    def take_session_lock(self):
        lock, self._session_lock = self._session_lock, None
        return lock

    def supplied_session_lock(self):
        return self._session_lock

    def closeEvent(self, event):
        if self._session_lock is not None:
            self._session_lock.unlock()
            self._session_lock = None
        super().closeEvent(event)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(56, 40, 56, 40)
        layout.setSpacing(16)
        self.title = QLabel()
        self.title.setTextFormat(Qt.TextFormat.PlainText)
        self.title.setObjectName("initTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint = QLabel()
        self.hint.setTextFormat(Qt.TextFormat.PlainText)
        self.hint.setObjectName("initHint")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint.setWordWrap(True)
        language_row = QHBoxLayout()
        self.language_label = QLabel()
        language_row.addStretch(1)
        language_row.addWidget(self.language_label)
        self.combo_language = QComboBox()
        self.combo_language.addItem("简体中文", "zh_CN")
        self.combo_language.addItem("English", "en_US")
        self.combo_language.setCurrentIndex(0 if i18n.language() == "zh_CN" else 1)
        self.combo_language.currentIndexChanged.connect(self._language_changed)
        language_row.addWidget(self.combo_language)
        language_row.addStretch(1)
        self.btn_template = QPushButton()
        self.btn_template.setObjectName("btnSecondary")
        self.btn_template.clicked.connect(self.on_download_template)
        self.btn_pick = QPushButton()
        self.btn_pick.setObjectName("btnPrimary")
        self.btn_pick.clicked.connect(self.on_pick_namelist)
        layout.addStretch(1)
        layout.addWidget(self.title)
        layout.addWidget(self.hint)
        layout.addLayout(language_row)
        layout.addSpacing(6)
        layout.addWidget(self.btn_template, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.btn_pick, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)
        self.retranslate_ui()

    def retranslate_ui(self):
        self.setWindowTitle(f"{window_title(i18n.tr('app.title'))} · {i18n.tr('init.title')}")
        self.title.setText(i18n.tr("init.title"))
        self.hint.setText(i18n.tr("init.hint"))
        self.language_label.setText(i18n.tr("menu.language"))
        self.btn_template.setText(i18n.tr("button.download_template"))
        self.btn_pick.setText(i18n.tr("button.choose_roster"))

    def _language_changed(self, index):
        candidate = self.combo_language.itemData(index)
        if not candidate or candidate == i18n.language():
            return
        previous = i18n.language()
        try:
            config.save_settings(language=candidate)
        except AppError as exc:
            self.combo_language.blockSignals(True)
            self.combo_language.setCurrentIndex(0 if previous == "zh_CN" else 1)
            self.combo_language.blockSignals(False)
            i18n.critical(self, i18n.tr("dialog.settings_save_failed"), error_text(exc))
            return
        i18n.set_language(candidate)
        self.retranslate_ui()

    def on_download_template(self):
        language = i18n.language()
        filename = i18n.tr("template.filename")
        path, _ = QFileDialog.getSaveFileName(self, i18n.tr("button.download_template"), filename, i18n.tr("template.filter"))
        if not path:
            return
        resource = paths.resource_path(f"resources/{'template-en.xlsx' if language == 'en_US' else 'template-zh.xlsx'}")
        try:
            shutil.copyfile(resource, path)
        except OSError as exc:
            i18n.critical(self, i18n.tr("dialog.error"), i18n.tr("dialog.template_save_failed", reason=exc))
            return
        i18n.information(self, i18n.tr("dialog.complete"), i18n.tr("status.template_saved", path=path))

    def _read_students(self, path):
        try:
            return excel_io.read_namelist(path)
        except AppError as exc:
            if exc.code != "excel.ambiguous_sheets":
                raise
            sheet = choose_sheet(self, exc.params.get("sheets", []))
            if not sheet:
                return None
            return excel_io.read_namelist(path, sheet_name=sheet)

    def on_pick_namelist(self):
        path, _ = QFileDialog.getOpenFileName(self, i18n.tr("button.choose_roster"), "", i18n.tr("template.filter"))
        if not path:
            return
        try:
            students = self.import_roster_path(path)
            if students is None:
                return
        except AppError as exc:
            notify = i18n.warning if exc.code == "excel.empty_namelist" else i18n.critical
            notify(self, i18n.tr("dialog.import_failed"), error_text(exc))
            return
        i18n.information(self, i18n.tr("dialog.complete"), i18n.tr("status.imported_students", count=len(students)))
        self.initialized.emit()

    def import_roster_path(self, path):
        """Validate and import a selected roster through the first-run path."""
        students = self._read_students(path)
        if students is None:
            return None
        if not students:
            raise AppError("excel.empty_namelist", path=str(path))
        expected = storage.fingerprint(self.target_path)
        if expected is not None:
            answer = i18n.question(self, i18n.tr("dialog.confirm"), i18n.tr("dialog.confirm_replace"), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return None
        excel_io.create_record_from_namelist(students, language=i18n.language(), path=self.target_path, expected_fingerprint=expected)
        return students
