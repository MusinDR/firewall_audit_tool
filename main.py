# main.py

import sys

from PyQt6.QtWidgets import QApplication

from gui.login.login_window import LoginWindow
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    with open("styles.qss", "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())
    login = LoginWindow(main_window_factory=lambda client: MainWindow(client))
    login.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
