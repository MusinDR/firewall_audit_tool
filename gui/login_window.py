# gui/login_window.py

from PyQt6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
)
from PyQt6.QtCore import QTimer
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import socket


class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Авторизация")
        self.resize(300, 160)

        self.server_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.handle_login)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("IP-адрес сервера:"))
        layout.addWidget(self.server_input)
        layout.addWidget(QLabel("Имя пользователя:"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        self.setLayout(layout)

        self.main_window = None

    def handle_login(self):
        server = self.server_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not server or not username or not password:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")
            return

        self.login_button.setEnabled(False)
        self.login_button.setText("Подключение...")

        try:
            socket.gethostbyname(server)  # Быстрая проверка DNS/IP
        except socket.gaierror:
            self.show_error("⛔ Невозможно разрешить адрес сервера.")
            return

        from checkpoint_client import CheckpointClient
        client = CheckpointClient(server, username, password)

        def try_login():
            return client.login()

        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(try_login)

        def check_result():
            if future.done():
                try:
                    result = future.result()
                    if result:
                        self.launch_main_window(client)
                    else:
                        self.show_error("🔒 Неверный логин или пароль.")
                except Exception as e:
                    self.show_error(f"⚠️ Ошибка: {str(e)}")
                finally:
                    executor.shutdown(wait=False)
            else:
                self.show_error("⏱ Сервер не отвечает.")
                executor.shutdown(wait=False)

        # Через 8 секунд проверим результат
        QTimer.singleShot(3000, check_result)

    def show_error(self, message: str):
        self.login_button.setEnabled(True)
        self.login_button.setText("Войти")
        QMessageBox.critical(self, "Ошибка подключения", message)

    def launch_main_window(self, client):
        from gui.main_window import MainWindow
        self.main_window = MainWindow(client)
        self.main_window.show()
        self.accept()
