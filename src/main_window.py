"""Main roll-call window and its recoverable session lifecycle."""

from __future__ import annotations

import datetime
import random
from pathlib import Path

from PySide6.QtCore import QLockFile, QTimer, Qt
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

import config
import excel_io
import i18n
import paths
import storage
import strategy
from config_dialog import ConfigDialog
from errors import AppError
from recovery_dialog import RecoveryDialog, choose_sheet, error_text
from record_actions import import_record

_FONT_FAMILIES = ["PingFang SC", "Microsoft YaHei", "Segoe UI"]
_MARQUEE_TICK_MS = 30
_DATE_CHECK_MS = 60_000


def current_date_string() -> str:
    return datetime.date.today().isoformat()


def acquire_session_lock(path):
    """Take the nonblocking whole-application lock for a data directory."""
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        lock = QLockFile(str(path.parent / ".rollcall-session.lock"))
        lock.setStaleLockTime(0)
        if not lock.tryLock(0):
            error = lock.error()
            if error == QLockFile.LockError.LockFailedError:
                raise AppError("storage_locked", path=str(path))
            raise AppError("storage_lock_failed", path=str(path), reason=getattr(error, "name", str(error)))
        return lock
    except AppError:
        raise
    except Exception as exc:
        raise AppError("storage_lock_failed", path=str(path)) from exc


def _load_with_sheet_choice(path, parent=None, sheet_name=None):
    try:
        return excel_io.load_record(path, sheet_name=sheet_name)
    except AppError as exc:
        if exc.code != "excel.ambiguous_sheets":
            raise
        selected = choose_sheet(parent, exc.params.get("sheets", []))
        if not selected:
            raise
        return excel_io.load_record(path, sheet_name=selected)


class MainWindow(QMainWindow):
    def __init__(self, data=None, *, data_path=None, sheet_name=None, acquire_lock=True, session_lock=None):
        super().__init__()
        self.setObjectName("root")
        self.setWindowTitle(i18n.tr("app.title"))
        self.resize(640, 480)
        self.setMinimumSize(640, 480)
        self.data_path = Path(data_path or paths.record_path())
        self._session_lock = session_lock
        # A supplied lock remains owned by the caller until construction has
        # completed successfully; this lets init/recovery retry safely.
        self._owns_session_lock = False
        if acquire_lock and session_lock is None:
            self._acquire_session_lock()
        try:
            self.data = data or _load_with_sheet_choice(self.data_path, self, sheet_name)
        except Exception:
            if self._owns_session_lock:
                self._release_session_lock()
            raise
        if self._session_lock is not None:
            self._owns_session_lock = True
        self.strategy, self.marquee_enabled, self.marquee_duration = self._read_settings()
        self.today = current_date_string()
        self.appeared = set()
        self.current = None
        self._finished = False
        self._date_refreshing = False
        self._pending_date_error = None
        self._build_menu()
        self._build_stack()

        self._marquee_timer = QTimer(self)
        self._marquee_timer.setInterval(_MARQUEE_TICK_MS)
        self._marquee_timer.timeout.connect(self._marquee_tick)
        self._reveal_timer = QTimer(self)
        self._reveal_timer.setSingleShot(True)
        self._reveal_timer.setInterval(self.marquee_duration)
        self._reveal_timer.timeout.connect(self._reveal)
        self._date_timer = QTimer(self)
        self._date_timer.setInterval(_DATE_CHECK_MS)
        self._date_timer.timeout.connect(self._check_date_timer)
        self._date_timer.start()
        self._marquee_list = []
        self._marquee_idx = 0

    def _read_settings(self):
        try:
            settings = config.load_settings()
        except AppError as exc:
            i18n.warning(self, i18n.tr("dialog.settings_read_failed"), error_text(exc))
            settings = config.defaults()
        return settings["strategy"], settings["marquee"], settings["marquee_duration"]

    def _acquire_session_lock(self):
        self._session_lock = acquire_session_lock(self.data_path)
        self._owns_session_lock = True

    def _release_session_lock(self):
        if self._session_lock is not None:
            try:
                self._session_lock.unlock()
            finally:
                self._session_lock = None

    def supplied_session_lock(self):
        """Return the lock for caller-owned handover without removing it."""
        return self._session_lock

    # ------------------------------------------------------------------ UI
    def _build_menu(self):
        bar = self.menuBar()
        self.file_menu = bar.addMenu("")
        backup = QAction(self)
        backup.triggered.connect(self.create_manual_backup)
        self.file_menu.addAction(backup)
        restore = QAction(self)
        restore.triggered.connect(self.restore_backup)
        self.file_menu.addAction(restore)
        import_action = QAction(self)
        import_action.triggered.connect(self.import_existing_record)
        self.file_menu.addAction(import_action)
        reload_action = QAction(self)
        reload_action.triggered.connect(self.reload_record)
        self.file_menu.addAction(reload_action)
        self._backup_action, self._restore_action = backup, restore
        self._import_action, self._reload_action = import_action, reload_action
        self.config_menu = bar.addMenu("")
        self._rules_action = QAction(self)
        self._rules_action.triggered.connect(self.open_config)
        self.config_menu.addAction(self._rules_action)
        self.language_menu = self.config_menu.addMenu("")
        self._zh_action = QAction(self)
        self._zh_action.setCheckable(True)
        self._en_action = QAction(self)
        self._en_action.setCheckable(True)
        self._zh_action.triggered.connect(lambda: self._change_language("zh_CN"))
        self._en_action.triggered.connect(lambda: self._change_language("en_US"))
        self.language_menu.addAction(self._zh_action)
        self.language_menu.addAction(self._en_action)
        self._about_action = QAction(self)
        self._about_action.triggered.connect(self.show_about)
        self.config_menu.addAction(self._about_action)

    def _build_stack(self):
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)
        start_page = QWidget()
        start_page.setObjectName("root")
        start_layout = QVBoxLayout(start_page)
        start_layout.setContentsMargins(24, 24, 24, 24)
        self.start_btn = QPushButton()
        self.start_btn.setObjectName("startButton")
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self.start_rollcall)
        start_layout.addStretch(1)
        start_layout.addWidget(self.start_btn, 0, Qt.AlignmentFlag.AlignCenter)
        start_layout.addStretch(1)

        roll_page = QWidget()
        roll_page.setObjectName("root")
        outer = QVBoxLayout(roll_page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        info = QWidget()
        info.setObjectName("root")
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(28, 16, 28, 10)
        info_layout.setSpacing(8)
        self.no_label = QLabel("")
        self.no_label.setObjectName("noLabel")
        self.no_label.setTextFormat(Qt.TextFormat.PlainText)
        self.no_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label = QLabel("")
        self.name_label.setObjectName("nameLabel")
        self.name_label.setTextFormat(Qt.TextFormat.PlainText)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)
        self.btn_present = QPushButton()
        self.btn_present.setObjectName("btnPresent")
        self.btn_leave = QPushButton()
        self.btn_leave.setObjectName("btnLeave")
        self.btn_absent = QPushButton()
        self.btn_absent.setObjectName("btnAbsent")
        for button in (self.btn_present, self.btn_leave, self.btn_absent):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_present.clicked.connect(lambda: self.on_record("到"))
        self.btn_leave.clicked.connect(lambda: self.on_record("假"))
        self.btn_absent.clicked.connect(lambda: self.on_record("旷"))
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_present)
        btn_row.addWidget(self.btn_leave)
        btn_row.addWidget(self.btn_absent)
        btn_row.addStretch(1)
        info_layout.addStretch(1)
        info_layout.addWidget(self.no_label)
        info_layout.addWidget(self.name_label)
        info_layout.addSpacing(10)
        info_layout.addLayout(btn_row)
        info_layout.addStretch(1)
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.Shape.HLine)
        bottom = QWidget()
        bottom.setObjectName("root")
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(24, 10, 24, 16)
        self.stop_btn = QPushButton()
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self.on_stop)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.stop_btn)
        outer.addWidget(info, 1)
        outer.addWidget(separator)
        outer.addWidget(bottom)
        self.stack.addWidget(start_page)
        self.stack.addWidget(roll_page)
        self.retranslate_ui()

    def retranslate_ui(self):
        """Refresh only presentation text; selection and timer state stay intact."""
        self.setWindowTitle(i18n.tr("app.title"))
        self.file_menu.setTitle(i18n.tr("menu.file"))
        self.config_menu.setTitle(i18n.tr("menu.config"))
        self.language_menu.setTitle(i18n.tr("menu.language"))
        self._backup_action.setText(i18n.tr("menu.backup"))
        self._restore_action.setText(i18n.tr("menu.restore"))
        self._import_action.setText(i18n.tr("menu.import"))
        self._reload_action.setText(i18n.tr("menu.reload"))
        self._rules_action.setText(i18n.tr("menu.rules"))
        self._zh_action.setText(i18n.tr("menu.language.zh"))
        self._en_action.setText(i18n.tr("menu.language.en"))
        self._zh_action.setChecked(i18n.language() == "zh_CN")
        self._en_action.setChecked(i18n.language() == "en_US")
        self._about_action.setText(i18n.tr("menu.about"))
        self.start_btn.setText(i18n.tr("button.start"))
        self.btn_present.setText(i18n.tr("button.present"))
        self.btn_leave.setText(i18n.tr("button.leave"))
        self.btn_absent.setText(i18n.tr("button.absent"))
        self.stop_btn.setText(i18n.tr("button.stop"))
        if self._finished:
            self.name_label.setText(i18n.tr("status.completed"))
        self._update_fonts()

    def _change_language(self, language):
        if language == i18n.language():
            return
        try:
            config.save_settings(language=language)
        except AppError as exc:
            i18n.critical(self, i18n.tr("dialog.settings_save_failed"), error_text(exc))
            self.retranslate_ui()
            return
        i18n.set_language(language)
        self.retranslate_ui()

    def show_about(self):
        i18n.information(self, i18n.tr("app.about"), i18n.tr("app.about_text"))

    # ------------------------------------------------------------- lifecycle
    def _check_date_timer(self):
        if current_date_string() != self.today:
            self._ensure_current_day()

    def _ensure_current_day(self) -> bool:
        new_day = current_date_string()
        if new_day == self.today:
            return True
        if self._date_refreshing:
            return False
        if self._pending_date_error == new_day:
            return False
        self._date_refreshing = True
        try:
            try:
                refreshed = _load_with_sheet_choice(self.data_path, self, self.data.sheet_name)
            except Exception as exc:
                self._pending_date_error = new_day
                i18n.warning(self, i18n.tr("dialog.date_read_failed"), error_text(exc))
                return False
            was_finished = self._finished
            self.data = refreshed
            self.today = new_day
            self._pending_date_error = None
            self.appeared.clear()
            self.current = None
            self._finished = False
            if was_finished:
                self.stack.setCurrentIndex(0)
            elif self.stack.currentIndex() == 1:
                self._begin_pick(check_date=False)
            i18n.information(self, i18n.tr("dialog.date_updated"), i18n.tr("status.date_updated", date=new_day))
            return False
        finally:
            self._date_refreshing = False

    # ------------------------------------------------------------- logic
    def start_rollcall(self):
        if not self._ensure_current_day():
            return
        self.appeared.clear()
        self._finished = False
        self.stack.setCurrentIndex(1)
        self._begin_pick(check_date=False)

    def _begin_pick(self, *, check_date=True):
        if check_date and not self._ensure_current_day():
            return
        target = strategy.next_student(self.data.students, self.today, self.strategy, self.appeared)
        if target is None:
            self._finish()
            return
        self.current = target
        self.appeared.add(target.id)
        self._finished = False
        self._set_record_buttons_enabled(False)
        self._update_fonts()
        if self.marquee_enabled and len(self.data.students) > 1:
            self._start_marquee()
        else:
            self._reveal()

    def _finish(self):
        self._stop_marquee()
        self.current = None
        self._finished = True
        self.no_label.setText("")
        self.name_label.setText(i18n.tr("status.completed"))
        self._set_record_buttons_enabled(False)
        self._update_fonts()

    def _start_marquee(self):
        self._stop_marquee()
        self._reveal_timer.setInterval(self.marquee_duration)
        self._marquee_list = list(self.data.students)
        random.shuffle(self._marquee_list)
        self._marquee_idx = 0
        if self._marquee_list:
            self._marquee_timer.start()
            self._reveal_timer.start()

    def _stop_marquee(self):
        self._marquee_timer.stop()
        self._reveal_timer.stop()

    def _marquee_tick(self):
        if self._marquee_list:
            student = self._marquee_list[self._marquee_idx]
            self.no_label.setText(student.no)
            self.name_label.setText(student.name)
            self._marquee_idx = (self._marquee_idx + 1) % len(self._marquee_list)

    def _reveal(self):
        self._stop_marquee()
        if self.current is not None:
            self.no_label.setText(self.current.no)
            self.name_label.setText(self.current.name)
            self._set_record_buttons_enabled(True)

    def on_record(self, value):
        if self.current is None or self._finished or not self._ensure_current_day():
            return
        student = self.current
        try:
            result = excel_io.write_record(student.no, self.today, value, data=self.data)
        except AppError as exc:
            if exc.code == "storage_conflict":
                self._recover_from_conflict(exc)
            else:
                i18n.critical(self, i18n.tr("dialog.save_failed"), error_text(exc))
            return
        except Exception as exc:
            i18n.critical(self, i18n.tr("dialog.save_failed"), error_text(exc))
            return
        self.data = result
        self._begin_pick(check_date=False)

    def _recover_from_conflict(self, error):
        i18n.warning(self, i18n.tr("dialog.read_failed"), i18n.tr("status.external_change"))
        self._stop_marquee()
        self.current = None
        self._set_record_buttons_enabled(False)
        try:
            self.reload_record(show_success=False)
        except Exception:
            pass

    def on_stop(self):
        answer = i18n.question(self, i18n.tr("dialog.confirm"), i18n.tr("dialog.confirm_stop"), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.close()

    def open_config(self):
        dialog = ConfigDialog(self, current=self.strategy, marquee=self.marquee_enabled, marquee_duration=self.marquee_duration)
        if not dialog.exec():
            return
        new_strategy = dialog.selected()
        new_marquee = dialog.marquee_selected()
        new_duration = dialog.marquee_duration_selected()
        new_language = dialog.language_selected()
        try:
            config.save_settings(strategy=new_strategy, marquee=new_marquee, marquee_duration=new_duration, language=new_language)
        except AppError as exc:
            i18n.critical(self, i18n.tr("dialog.settings_save_failed"), error_text(exc))
            return
        strategy_changed = new_strategy != self.strategy
        self.strategy, self.marquee_enabled, self.marquee_duration = new_strategy, new_marquee, new_duration
        if new_language != i18n.language():
            i18n.set_language(new_language)
            self.retranslate_ui()
        self._reveal_timer.setInterval(self.marquee_duration)
        if strategy_changed:
            self._refresh_after_strategy_change()

    def _refresh_after_strategy_change(self):
        if self.stack.currentIndex() == 1 and self.current is not None:
            self.appeared.discard(self.current.id)
            self.current = None
            self._begin_pick()

    # ---------------------------------------------------------- file actions
    def create_manual_backup(self):
        try:
            backup = storage.create_backup(self.data_path, kind="manual")
        except AppError as exc:
            i18n.critical(self, i18n.tr("dialog.backup_failed"), error_text(exc))
            return None
        i18n.information(self, i18n.tr("dialog.backup_complete"), i18n.tr("status.backup_created", name=backup.name))
        return backup

    def restore_backup(self):
        dialog = RecoveryDialog(self.data_path, AppError("storage_invalid_backup", path=str(self.data_path)), self)
        dialog.recovered.connect(self._apply_restored_data)
        dialog.exec()

    def import_existing_record(self):
        source_name, _ = QFileDialog.getOpenFileName(self, i18n.tr("menu.import"), "", i18n.tr("record.filter"))
        if not source_name:
            return None
        source = Path(source_name)
        try:
            source_data = _load_with_sheet_choice(source, self)
        except Exception as exc:
            i18n.critical(self, i18n.tr("dialog.import_failed"), error_text(exc))
            return None
        try:
            imported = import_record(
                source, self.data_path, source_data,
                confirm=lambda: i18n.question(
                    self, i18n.tr("dialog.confirm"), i18n.tr("dialog.confirm_replace"),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                ) == QMessageBox.StandardButton.Yes,
            )
            if imported is None:
                return None
            self._apply_restored_data(imported)
            i18n.information(self, i18n.tr("dialog.import_complete"), i18n.tr("status.imported"))
            return imported
        except AppError as exc:
            i18n.critical(self, i18n.tr("dialog.import_failed"), error_text(exc))
            return None

    def _apply_restored_data(self, data):
        try:
            self.data = data or _load_with_sheet_choice(self.data_path, self)
        except Exception as exc:
            i18n.critical(self, i18n.tr("dialog.restore_read_failed"), error_text(exc))
            return
        self.appeared.clear()
        self.current = None
        self._finished = False
        if self.stack.currentIndex() == 1:
            self._begin_pick()

    def reload_record(self, *, show_success=True):
        try:
            data = _load_with_sheet_choice(self.data_path, self, self.data.sheet_name)
        except Exception as exc:
            i18n.critical(self, i18n.tr("dialog.reload_failed"), error_text(exc))
            raise
        self.data = data
        self._pending_date_error = None
        self.appeared.clear()
        self.current = None
        self._finished = False
        if self.stack.currentIndex() == 1:
            self._begin_pick(check_date=False)
        if show_success:
            i18n.information(self, i18n.tr("dialog.reload_complete"), i18n.tr("status.reloaded"))
        return data

    def _set_record_buttons_enabled(self, enabled):
        for button in (self.btn_present, self.btn_leave, self.btn_absent):
            button.setEnabled(enabled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_fonts()

    def _update_fonts(self):
        height = self.height()
        if self._finished:
            font = QFont()
            font.setFamilies(_FONT_FAMILIES)
            font.setPixelSize(max(20, min(32, int(height * 0.055))))
            font.setWeight(QFont.Weight.DemiBold)
            self.name_label.setFont(font)
            return
        name_font = QFont()
        name_font.setFamilies(_FONT_FAMILIES)
        name_font.setPixelSize(max(34, min(140, int(height * 0.16))))
        name_font.setWeight(QFont.Weight.DemiBold)
        self.name_label.setFont(name_font)
        no_font = QFont()
        no_font.setFamilies(_FONT_FAMILIES)
        no_font.setPixelSize(max(20, min(72, int(height * 0.085))))
        self.no_label.setFont(no_font)

    def closeEvent(self, event):
        self._stop_marquee()
        self._date_timer.stop()
        self._release_session_lock()
        super().closeEvent(event)
