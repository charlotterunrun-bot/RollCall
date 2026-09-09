"""First-run and empty-record initialization window."""

import shutil
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

import excel_io
import paths
import storage
from errors import AppError
from recovery_dialog import choose_sheet, error_text
from main_window import acquire_session_lock


class InitWindow(QWidget):
    initialized = Signal()

    def __init__(self, *, target_path=None, session_lock=None, acquire_lock=False):
        super().__init__()
        self.setObjectName("root")
        self.setWindowTitle("课堂点名 · 初始化")
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
        layout.setContentsMargins(56, 48, 56, 48)
        layout.setSpacing(16)
        title = QLabel("欢迎使用课堂点名")
        title.setTextFormat(Qt.TextFormat.PlainText)
        title.setObjectName("initTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint = QLabel("首次使用：请先「下载模板」，用 Excel 填写学生信息\n（花名册须包含四列：序号 / 学号 / 姓名 / 班级），\n然后「选择花名册文件」导入。")
        hint.setTextFormat(Qt.TextFormat.PlainText)
        hint.setObjectName("initHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_template = QPushButton("下载模板")
        self.btn_template.setObjectName("btnSecondary")
        self.btn_template.clicked.connect(self.on_download_template)
        self.btn_pick = QPushButton("选择花名册文件")
        self.btn_pick.setObjectName("btnPrimary")
        self.btn_pick.clicked.connect(self.on_pick_namelist)
        layout.addStretch(1)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addSpacing(10)
        layout.addWidget(self.btn_template, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.btn_pick, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)

    def on_download_template(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存模板", "namelist模板.xls", "Excel 文件 (*.xls)")
        if not path:
            return
        try:
            shutil.copyfile(paths.resource_path(paths.TEMPLATE_NAME), path)
        except OSError as exc:
            QMessageBox.critical(self, "错误", f"保存模板失败：\n{exc}")
            return
        QMessageBox.information(self, "完成", f"模板已保存到：\n{path}")

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
        path, _ = QFileDialog.getOpenFileName(self, "选择花名册", "", "Excel 文件 (*.xlsx *.xls)")
        if not path:
            return
        try:
            students = self._read_students(path)
            if students is None:
                return
            if not students:
                QMessageBox.warning(self, "名单为空", "花名册没有学生记录，请补充后再导入。")
                return
            expected = storage.fingerprint(self.target_path)
            if expected is not None:
                answer = QMessageBox.question(self, "确认替换", "当前记录已存在，导入将替换它并先创建备份。是否继续？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                if answer != QMessageBox.StandardButton.Yes:
                    return
            excel_io.create_record_from_namelist(students, path=self.target_path, expected_fingerprint=expected)
        except AppError as exc:
            QMessageBox.critical(self, "导入失败", error_text(exc))
            return
        QMessageBox.information(self, "完成", f"已导入 {len(students)} 名学生。")
        self.initialized.emit()
