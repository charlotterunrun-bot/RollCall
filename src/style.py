"""Apple-like minimal light stylesheet."""

STYLESHEET = """
* {
    font-family: "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif;
    color: #1D1D1F;
}

QMainWindow, QDialog, QWidget#root {
    background-color: #F5F5F7;
}

QLabel {
    background: transparent;
    color: #1D1D1F;
}

/* ---- Menu bar ---- */
QMenuBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E5E5EA;
    padding: 2px 6px;
    font-size: 14px;
}
QMenuBar::item {
    padding: 5px 12px;
    background: transparent;
    border-radius: 6px;
}
QMenuBar::item:selected {
    background: #E8E8ED;
}
QMenu {
    background-color: #FFFFFF;
    border: 1px solid #E5E5EA;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    padding: 7px 26px 7px 16px;
    border-radius: 5px;
}
QMenu::item:selected {
    background: #E8E8ED;
}

/* ---- Generic buttons ---- */
QPushButton {
    background-color: #FFFFFF;
    color: #1D1D1F;
    border: 1px solid #D2D2D7;
    border-radius: 12px;
    padding: 8px 20px;
    font-size: 15px;
}
QPushButton:hover {
    background-color: #F2F2F7;
}
QPushButton:pressed {
    background-color: #E8E8ED;
}
QPushButton:disabled {
    color: #AEAEB2;
    border-color: #E5E5EA;
    background-color: #F5F5F7;
}

/* ---- Big start button ---- */
QPushButton#startButton {
    background-color: #1D1D1F;
    color: #FFFFFF;
    border: none;
    border-radius: 22px;
    padding: 20px 52px;
    font-size: 26px;
    font-weight: 600;
}
QPushButton#startButton:hover {
    background-color: #3A3A3C;
}
QPushButton#startButton:pressed {
    background-color: #000000;
}

/* ---- Record buttons ---- */
QPushButton#btnPresent {
    background-color: #34C759;
    color: #FFFFFF;
    border: none;
    border-radius: 14px;
    padding: 14px 34px;
    font-size: 19px;
    font-weight: 600;
}
QPushButton#btnPresent:hover { background-color: #2BB44E; }
QPushButton#btnPresent:pressed { background-color: #239C42; }
QPushButton#btnPresent:disabled { background-color: #C8EBD2; }

QPushButton#btnLeave {
    background-color: #FF9500;
    color: #FFFFFF;
    border: none;
    border-radius: 14px;
    padding: 14px 34px;
    font-size: 19px;
    font-weight: 600;
}
QPushButton#btnLeave:hover { background-color: #E88700; }
QPushButton#btnLeave:pressed { background-color: #C97500; }
QPushButton#btnLeave:disabled { background-color: #FFE1B8; }

QPushButton#btnAbsent {
    background-color: #FF3B30;
    color: #FFFFFF;
    border: none;
    border-radius: 14px;
    padding: 14px 34px;
    font-size: 19px;
    font-weight: 600;
}
QPushButton#btnAbsent:hover { background-color: #E63328; }
QPushButton#btnAbsent:pressed { background-color: #C52B21; }
QPushButton#btnAbsent:disabled { background-color: #FFC4C1; }

/* ---- Stop button (isolated, muted) ---- */
QPushButton#stopButton {
    background-color: #FFFFFF;
    color: #6E6E73;
    border: 1px solid #C7C7CC;
    border-radius: 12px;
    padding: 9px 22px;
    font-size: 15px;
}
QPushButton#stopButton:hover {
    background-color: #F2F2F7;
    color: #1D1D1F;
}

/* ---- Separator ---- */
QFrame#separator {
    background-color: #E5E5EA;
    max-height: 1px;
    border: none;
}

/* ---- Init page ---- */
QLabel#initTitle {
    font-size: 26px;
    font-weight: 600;
    color: #1D1D1F;
}
QLabel#initHint {
    font-size: 15px;
    color: #6E6E73;
}
QPushButton#btnPrimary {
    background-color: #1D1D1F;
    color: #FFFFFF;
    border: none;
    border-radius: 14px;
    padding: 12px 28px;
    font-size: 17px;
    font-weight: 600;
}
QPushButton#btnPrimary:hover { background-color: #3A3A3C; }
QPushButton#btnSecondary {
    background-color: #FFFFFF;
    color: #1D1D1F;
    border: 1px solid #D2D2D7;
    border-radius: 14px;
    padding: 12px 28px;
    font-size: 17px;
}
QPushButton#btnSecondary:hover { background-color: #F2F2F7; }

/* ---- Radio buttons ---- */
QRadioButton {
    font-size: 15px;
    color: #1D1D1F;
    spacing: 10px;
    padding: 3px 0;
}
QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 1px solid #C7C7CC;
    background-color: #FFFFFF;
}
QRadioButton::indicator:hover {
    border-color: #1D1D1F;
}
QRadioButton::indicator:checked {
    background-color: #1D1D1F;
    border: 1px solid #1D1D1F;
}

QDialogButtonBox QPushButton {
    min-width: 84px;
    padding: 8px 18px;
}
"""

LABEL_STYLE = {
    "no": "#6E6E73",
    "name": "#1D1D1F",
}
