"""Application entry point."""
import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

import excel_io
from init_window import InitWindow
from main_window import MainWindow
from style import STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("课堂点名")
    app.setStyleSheet(STYLESHEET)

    font = QFont()
    font.setFamilies(["PingFang SC", "Microsoft YaHei", "Segoe UI"])
    font.setPixelSize(15)
    app.setFont(font)

    if excel_io.is_first_run():
        init_win = InitWindow()
        main_holder = {}

        def on_initialized():
            main_win = MainWindow()
            main_holder["win"] = main_win
            main_win.show()
            init_win.close()

        init_win.initialized.connect(on_initialized)
        init_win.show()
    else:
        main_win = MainWindow()
        main_win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
