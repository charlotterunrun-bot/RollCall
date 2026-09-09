"""Application entry point with explicit startup recovery states."""

import sys
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

import config
import excel_io
import i18n
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
            i18n.critical(window, i18n.tr("dialog.startup_failed"), error_text(exc))
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
    source_name, _ = QFileDialog.getOpenFileName(parent, i18n.tr("menu.import"), "", i18n.tr("record.filter"))
    if not source_name:
        return None
    source = Path(source_name)
    try:
        source_data = _load_with_sheet_choice(source, parent)
        def confirm():
            answer = i18n.question(parent, i18n.tr("dialog.confirm"), i18n.tr("dialog.confirm_replace"), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            return answer == QMessageBox.StandardButton.Yes

        return import_record(source, target, source_data, confirm=confirm)
    except AppError as exc:
        i18n.critical(parent, i18n.tr("dialog.import_failed"), error_text(exc))
        return None
    except OSError as exc:
        i18n.critical(parent, i18n.tr("dialog.import_failed"), error_text(AppError("storage_read_failed", path=str(source))))
        return None


def main():
    app = QApplication(sys.argv)
    startup_config_error = i18n.initialize()
    app.setApplicationName(i18n.tr("app.title"))
    app.setStyleSheet(STYLESHEET)
    font = QFont()
    font.setFamilies(["PingFang SC", "Microsoft YaHei", "Segoe UI"])
    font.setPixelSize(15)
    app.setFont(font)

    if startup_config_error is not None:
        i18n.warning(None, i18n.tr("dialog.settings_read_failed"), error_text(startup_config_error))

    try:
        session_lock = acquire_session_lock(paths.record_path())
    except AppError as exc:
        i18n.critical(None, i18n.tr("dialog.startup_failed"), error_text(exc))
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
                i18n.critical(dialog, i18n.tr("dialog.startup_recovery_failed"), error_text(exc))

        def retry():
            try:
                state = excel_io.probe_record(paths.record_path())
                if state in {"missing", "empty"}:
                    holder.update(_show_init(app, session_lock=session_lock))
                else:
                    holder["main"] = _show_main(session_lock=session_lock)
                dialog.accept()
            except AppError as exc:
                i18n.critical(dialog, i18n.tr("dialog.read_failed"), error_text(exc))

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
            i18n.critical(None, i18n.tr("dialog.startup_failed"), error_text(exc))
            return 0
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
