"""Roll-call rule configuration dialog."""
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)

import config


class ConfigDialog(QDialog):
    def __init__(self, parent=None, current=None, marquee=True,
                 marquee_duration=config.DEFAULT_MARQUEE_DURATION):
        super().__init__(parent)
        self.setWindowTitle("点名规则")
        self.setModal(True)
        self.setMinimumWidth(400)
        self._current = current or config.load_strategy()
        self._marquee = marquee
        self._marquee_duration = marquee_duration
        self._radios = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 18)
        layout.setSpacing(12)

        title = QLabel("选择点名规则")
        title.setStyleSheet("font-size: 17px; font-weight: 600; color: #1D1D1F;")
        layout.addWidget(title)

        self._group = QButtonGroup(self)
        for key in config.STRATEGY_ORDER:
            rb = QRadioButton(config.STRATEGY_LABELS[key])
            if key == self._current:
                rb.setChecked(True)
            self._group.addButton(rb)
            self._radios[key] = rb
            layout.addWidget(rb)

        layout.addSpacing(4)

        self.chk_marquee = QCheckBox("启用走马灯抽选效果")
        self.chk_marquee.setChecked(self._marquee)
        layout.addWidget(self.chk_marquee)

        dur_row = QHBoxLayout()
        dur_row.setContentsMargins(20, 0, 0, 0)
        dur_row.setSpacing(8)
        dur_row.addWidget(QLabel("自动停下时长："))
        self.spin_duration = QSpinBox()
        self.spin_duration.setRange(config.MARQUEE_DURATION_MIN, config.MARQUEE_DURATION_MAX)
        self.spin_duration.setValue(self._marquee_duration)
        self.spin_duration.setSuffix(" ms")
        dur_row.addWidget(self.spin_duration)
        hint = QLabel(
            f"（请输入 {config.MARQUEE_DURATION_MIN}～{config.MARQUEE_DURATION_MAX} 的整数，单位毫秒）"
        )
        hint.setStyleSheet("color: #6E6E73; font-size: 12px;")
        dur_row.addWidget(hint)
        dur_row.addStretch(1)
        layout.addLayout(dur_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("确定")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addSpacing(6)
        layout.addWidget(buttons)

    def selected(self):
        for key, rb in self._radios.items():
            if rb.isChecked():
                return key
        return config.DEFAULT_STRATEGY

    def marquee_selected(self):
        return self.chk_marquee.isChecked()

    def marquee_duration_selected(self):
        return self.spin_duration.value()
