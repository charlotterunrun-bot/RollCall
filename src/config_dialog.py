"""Roll-call rule configuration dialog."""
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)

import config
import i18n


class ConfigDialog(QDialog):
    def __init__(self, parent=None, current=None, marquee=True,
                 marquee_duration=config.DEFAULT_MARQUEE_DURATION):
        super().__init__(parent)
        self._title_label = None
        self.setModal(True)
        self.setMinimumWidth(540)
        self._current = current or config.load_strategy()
        self._marquee = marquee
        self._marquee_duration = marquee_duration
        self._radios = {}
        self._language_label = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 18)
        layout.setSpacing(12)

        self._title_label = QLabel()
        self._title_label.setStyleSheet("font-size: 17px; font-weight: 600; color: #1D1D1F;")
        layout.addWidget(self._title_label)

        self._group = QButtonGroup(self)
        for key in config.STRATEGY_ORDER:
            rb = QRadioButton()
            if key == self._current:
                rb.setChecked(True)
            self._group.addButton(rb)
            self._radios[key] = rb
            layout.addWidget(rb)

        layout.addSpacing(4)

        self.chk_marquee = QCheckBox()
        self.chk_marquee.setChecked(self._marquee)
        layout.addWidget(self.chk_marquee)

        dur_row = QHBoxLayout()
        dur_row.setContentsMargins(20, 0, 0, 0)
        dur_row.setSpacing(8)
        self._duration_label = QLabel()
        dur_row.addWidget(self._duration_label)
        self.spin_duration = QSpinBox()
        self.spin_duration.setRange(config.MARQUEE_DURATION_MIN, config.MARQUEE_DURATION_MAX)
        self.spin_duration.setValue(self._marquee_duration)
        self.spin_duration.setSuffix(" ms")
        dur_row.addWidget(self.spin_duration)
        self._duration_hint = QLabel()
        self._duration_hint.setStyleSheet("color: #6E6E73; font-size: 12px;")
        self._duration_hint.setWordWrap(True)
        dur_row.addWidget(self._duration_hint)
        dur_row.addStretch(1)
        layout.addLayout(dur_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addSpacing(6)
        layout.addWidget(buttons)
        language_row = QHBoxLayout()
        self._language_label = QLabel()
        language_row.addWidget(self._language_label)
        self.combo_language = QComboBox()
        self.combo_language.addItem("简体中文", "zh_CN")
        self.combo_language.addItem("English", "en_US")
        self.combo_language.setCurrentIndex(0 if i18n.language() == "zh_CN" else 1)
        language_row.addWidget(self.combo_language)
        language_row.addStretch(1)
        layout.insertLayout(1, language_row)
        self.retranslate_ui()

    def retranslate_ui(self):
        self.setWindowTitle(i18n.tr("config.title"))
        self._title_label.setText(i18n.tr("config.choose_rule"))
        for key, radio in self._radios.items():
            radio.setText(i18n.tr(f"strategy.{key}"))
            radio.setToolTip(i18n.tr(f"strategy.{key}_hint"))
        self.chk_marquee.setText(i18n.tr("config.marquee"))
        self._duration_label.setText(i18n.tr("config.duration"))
        self._duration_hint.setText(i18n.tr("config.duration_hint", minimum=config.MARQUEE_DURATION_MIN, maximum=config.MARQUEE_DURATION_MAX))
        self._language_label.setText(i18n.tr("menu.language"))
        self._ok_button.setText(i18n.tr("button.ok"))
        self._cancel_button.setText(i18n.tr("button.cancel"))

    def selected(self):
        for key, rb in self._radios.items():
            if rb.isChecked():
                return key
        return config.DEFAULT_STRATEGY

    def marquee_selected(self):
        return self.chk_marquee.isChecked()

    def marquee_duration_selected(self):
        return self.spin_duration.value()

    def language_selected(self):
        return self.combo_language.currentData()
