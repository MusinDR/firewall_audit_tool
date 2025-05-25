import sys

from PyQt6.QtWidgets import QApplication

from gui.login_window import LoginWindow
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    login = LoginWindow(main_window_factory=lambda client: MainWindow(client))
    login.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
