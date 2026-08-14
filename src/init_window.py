"""First-run initialization window."""
import shutil

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import excel_io
import paths


class InitWindow(QWidget):
    initialized = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("root")
        self.setWindowTitle("课堂点名 · 初始化")
        self.resize(640, 480)
        self.setMinimumSize(560, 420)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(56, 48, 56, 48)
        layout.setSpacing(16)

        title = QLabel("欢迎使用课堂点名")
        title.setObjectName("initTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hint = QLabel(
            "首次使用：请先「下载模板」，用 Excel 填写学生信息\n"
            "（花名册须包含四列：序号 / 学号 / 姓名 / 班级），\n"
            "然后「选择花名册文件」导入。"
        )
        hint.setObjectName("initHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_template = QPushButton("下载模板")
        self.btn_template.setObjectName("btnSecondary")
        self.btn_template.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_template.clicked.connect(self.on_download_template)

        self.btn_pick = QPushButton("选择花名册文件")
        self.btn_pick.setObjectName("btnPrimary")
        self.btn_pick.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pick.clicked.connect(self.on_pick_namelist)

        layout.addStretch(1)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addSpacing(10)
        layout.addWidget(self.btn_template, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.btn_pick, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)

    def on_download_template(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "保存模板", "namelist模板.xls", "Excel 文件 (*.xls)"
        )
        if not path:
            return
        try:
            shutil.copyfile(paths.resource_path(paths.TEMPLATE_NAME), path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "错误", f"保存模板失败：\n{exc}")
            return
        QMessageBox.information(self, "完成", f"模板已保存到：\n{path}")

    def on_pick_namelist(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择花名册", "", "Excel 文件 (*.xlsx *.xls)"
        )
        if not path:
            return
        try:
            students = excel_io.read_namelist(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "导入失败", str(exc))
            return
        try:
            excel_io.create_record_from_namelist(students)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "创建记录失败", str(exc))
            return
        QMessageBox.information(self, "完成", f"已导入 {len(students)} 名学生。")
        self.initialized.emit()
