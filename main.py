import sys
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog
from checkpoint_client import CheckpointClient
from gui.login_window import LoginDialog
from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    login = LoginDialog()
    if login.exec() == QDialog.DialogCode.Accepted:
        ip, user, password = login.get_credentials()
        client = CheckpointClient(ip, user, password)

        if client.login():
            window = MainWindow(client)
            window.show()
            sys.exit(app.exec())  # <— это важно
        else:
            QMessageBox.critical(None, "Ошибка входа", "Неверные данные")
            sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
