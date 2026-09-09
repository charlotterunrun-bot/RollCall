"""Application entry point with explicit startup recovery states."""

import sys
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

import config
import excel_io
import paths
from errors import AppError
from init_window import InitWindow
from main_window import MainWindow, _load_with_sheet_choice, acquire_session_lock
from recovery_dialog import RecoveryDialog, error_text
from style import STYLESHEET
from record_actions import import_record


def _show_init(app, *, session_lock=None):
    window = InitWindow(session_lock=session_lock)
    holder = {"window": window}

    def on_initialized():
        try:
            main_window = MainWindow(session_lock=window.supplied_session_lock())
        except AppError as exc:
            QMessageBox.critical(window, "启动失败", error_text(exc))
            return
        window.take_session_lock()
        holder["main"] = main_window
        main_window.show()
        window.close()

    window.initialized.connect(on_initialized)
    window.show()
    return holder


def _show_main(data=None, *, session_lock=None):
    window = MainWindow(data=data, session_lock=session_lock)
    window.show()
    return window


def _import_existing_record(parent, target):
    """Import a validated existing record, retaining the target on failure."""
    source_name, _ = QFileDialog.getOpenFileName(parent, "导入已有记录", "", "Excel 文件 (*.xlsx)")
    if not source_name:
        return None
    source = Path(source_name)
    try:
        source_data = _load_with_sheet_choice(source, parent)
        def confirm():
            answer = QMessageBox.question(parent, "确认替换", "导入将替换当前记录，并先保留备份。是否继续？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            return answer == QMessageBox.StandardButton.Yes

        return import_record(source, target, source_data, confirm=confirm)
    except AppError as exc:
        QMessageBox.critical(parent, "导入失败", error_text(exc))
        return None
    except OSError as exc:
        QMessageBox.critical(parent, "导入失败", error_text(AppError("storage_read_failed", path=str(source))))
        return None


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("课堂点名")
    app.setStyleSheet(STYLESHEET)
    font = QFont()
    font.setFamilies(["PingFang SC", "Microsoft YaHei", "Segoe UI"])
    font.setPixelSize(15)
    app.setFont(font)

    try:
        session_lock = acquire_session_lock(paths.record_path())
    except AppError as exc:
        QMessageBox.critical(None, "启动失败", error_text(exc))
        return 0
    try:
        state = excel_io.probe_record(paths.record_path())
    except AppError as error:
        dialog = RecoveryDialog(paths.record_path(), error)
        holder = {}

        def recovered(data):
            try:
                holder["main"] = _show_main(data=data, session_lock=session_lock)
                dialog.accept()
            except AppError as exc:
                QMessageBox.critical(dialog, "恢复后启动失败", error_text(exc))

        def retry():
            try:
                state = excel_io.probe_record(paths.record_path())
                if state in {"missing", "empty"}:
                    holder.update(_show_init(app, session_lock=session_lock))
                else:
                    holder["main"] = _show_main(session_lock=session_lock)
                dialog.accept()
            except AppError as exc:
                QMessageBox.critical(dialog, "读取失败", error_text(exc))

        def import_record():
            data = _import_existing_record(dialog, Path(paths.record_path()))
            if data is not None:
                holder["main"] = _show_main(data=data, session_lock=session_lock)
                dialog.accept()

        dialog.retry_requested.connect(retry)
        dialog.import_requested.connect(import_record)
        dialog.recovered.connect(recovered)
        dialog.exec()
        if not holder:
            session_lock.unlock()
            return 0
        return app.exec()
    if state in {"missing", "empty"}:
        app._rollcall_holder = _show_init(app, session_lock=session_lock)
    else:
        try:
            app._rollcall_holder = {"main": _show_main(session_lock=session_lock)}
        except AppError as exc:
            session_lock.unlock()
            QMessageBox.critical(None, "启动失败", error_text(exc))
            return 0
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
