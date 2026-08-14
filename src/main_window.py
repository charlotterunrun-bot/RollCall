"""Main roll-call window."""
import datetime
import random

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

import config
import excel_io
import strategy
from config_dialog import ConfigDialog

_FONT_FAMILIES = ["PingFang SC", "Microsoft YaHei", "Segoe UI"]
_MARQUEE_TICK_MS = 30


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("root")
        self.setWindowTitle("课堂点名")
        self.resize(640, 480)
        self.setMinimumSize(640, 480)

        self.data = excel_io.load_record()
        self.strategy = config.load_strategy()
        self.marquee_enabled = config.load_marquee()
        self.marquee_duration = config.load_marquee_duration()
        self.today = datetime.date.today().strftime("%Y-%m-%d")
        self.appeared = set()
        self.current = None
        self._finished = False

        self._build_menu()
        self._build_stack()

        self._marquee_timer = QTimer(self)
        self._marquee_timer.setInterval(_MARQUEE_TICK_MS)
        self._marquee_timer.timeout.connect(self._marquee_tick)
        self._reveal_timer = QTimer(self)
        self._reveal_timer.setSingleShot(True)
        self._reveal_timer.setInterval(self.marquee_duration)
        self._reveal_timer.timeout.connect(self._reveal)
        self._marquee_list = []
        self._marquee_idx = 0

    # ------------------------------------------------------------------ UI
    def _build_menu(self):
        bar = self.menuBar()
        menu = bar.addMenu("配置")
        action = QAction("点名规则...", self)
        action.triggered.connect(self.open_config)
        menu.addAction(action)

    def _build_stack(self):
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        # Page 0: start
        start_page = QWidget()
        start_page.setObjectName("root")
        start_layout = QVBoxLayout(start_page)
        start_layout.setContentsMargins(24, 24, 24, 24)
        self.start_btn = QPushButton("现在开始点名啦！")
        self.start_btn.setObjectName("startButton")
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self.start_rollcall)
        start_layout.addStretch(1)
        start_layout.addWidget(self.start_btn, 0, Qt.AlignmentFlag.AlignCenter)
        start_layout.addStretch(1)

        # Page 1: roll-call
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
        self.no_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label = QLabel("")
        self.name_label.setObjectName("nameLabel")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)
        self.btn_present = QPushButton("已到")
        self.btn_present.setObjectName("btnPresent")
        self.btn_leave = QPushButton("请假")
        self.btn_leave.setObjectName("btnLeave")
        self.btn_absent = QPushButton("未到")
        self.btn_absent.setObjectName("btnAbsent")
        for b in (self.btn_present, self.btn_leave, self.btn_absent):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
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
        self.stop_btn = QPushButton("停止并退出")
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

    # ------------------------------------------------------------- logic
    def start_rollcall(self):
        self.appeared.clear()
        self._finished = False
        self.stack.setCurrentIndex(1)
        self._begin_pick()

    def _begin_pick(self):
        target = strategy.next_student(
            self.data.students, self.today, self.strategy, self.appeared
        )
        if target is None:
            self._finish()
            return
        self.current = target
        self.appeared.add(target.id)
        self._finished = False
        self._set_record_buttons_enabled(False)  # enabled only after reveal
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
        self.name_label.setText("今日全部点名完成！")
        self._set_record_buttons_enabled(False)
        self._update_fonts()

    def _start_marquee(self):
        self._stop_marquee()
        self._reveal_timer.setInterval(self.marquee_duration)
        # The marquee scrolls through the FULL roster (all students),
        # independent of the selection strategy, so suspense is preserved even
        # when only a few students remain selectable. The strategy only decides
        # the hidden target (self.current) revealed when the timer fires.
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
        if not self._marquee_list:
            return
        s = self._marquee_list[self._marquee_idx]
        self.no_label.setText(s.no)
        self.name_label.setText(s.name)
        self._marquee_idx = (self._marquee_idx + 1) % len(self._marquee_list)

    def _reveal(self):
        self._stop_marquee()
        if self.current is not None:
            self.no_label.setText(self.current.no)
            self.name_label.setText(self.current.name)
            self._set_record_buttons_enabled(True)

    def on_record(self, value):
        if self.current is None or self._finished:
            return
        s = self.current
        try:
            excel_io.write_record(s.no, self.today, value)
            s.records[self.today] = value
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "保存失败", f"写入记录失败：\n{exc}")
            return
        self._begin_pick()

    def on_stop(self):
        answer = QMessageBox.question(
            self,
            "确认",
            "确定要停止并退出吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.close()

    def open_config(self):
        dialog = ConfigDialog(
            self,
            current=self.strategy,
            marquee=self.marquee_enabled,
            marquee_duration=self.marquee_duration,
        )
        if dialog.exec():
            self.strategy = dialog.selected()
            self.marquee_enabled = dialog.marquee_selected()
            self.marquee_duration = dialog.marquee_duration_selected()
            config.save_settings(
                strategy=self.strategy,
                marquee=self.marquee_enabled,
                marquee_duration=self.marquee_duration,
            )
            self._refresh_after_strategy_change()

    def _refresh_after_strategy_change(self):
        # A student is currently shown but not yet recorded. Re-pick under the
        # new strategy so the display conforms to it, without recording anything
        # for the student that was on screen.
        if self.stack.currentIndex() == 1 and self.current is not None:
            self.appeared.discard(self.current.id)
            self.current = None
            self._begin_pick()

    def _set_record_buttons_enabled(self, enabled):
        for b in (self.btn_present, self.btn_leave, self.btn_absent):
            b.setEnabled(enabled)

    # ----------------------------------------------------------- fonts
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_fonts()

    def _update_fonts(self):
        h = self.height()

        # "今日全部点名完成！" is a status message, not a student name, so use
        # a much smaller font that always fits the window width.
        if self._finished:
            done_px = max(20, min(32, int(h * 0.055)))
            done_font = QFont()
            done_font.setFamilies(_FONT_FAMILIES)
            done_font.setPixelSize(done_px)
            done_font.setWeight(QFont.Weight.DemiBold)
            self.name_label.setFont(done_font)
            return

        name_px = max(34, min(140, int(h * 0.16)))
        no_px = max(20, min(72, int(h * 0.085)))

        name_font = QFont()
        name_font.setFamilies(_FONT_FAMILIES)
        name_font.setPixelSize(name_px)
        name_font.setWeight(QFont.Weight.DemiBold)
        self.name_label.setFont(name_font)

        no_font = QFont()
        no_font.setFamilies(_FONT_FAMILIES)
        no_font.setPixelSize(no_px)
        no_font.setWeight(QFont.Weight.Normal)
        self.no_label.setFont(no_font)
