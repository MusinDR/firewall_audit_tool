# gui/login/login_window.py

import socket
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from infrastructure.checkpoint_api_client import CheckpointClient
from infrastructure.logger import logger


class LoginWindow(QDialog):
    def __init__(self, main_window_factory):
        super().__init__()
        self.setWindowTitle("Авторизация")
        self.setFixedSize(320, 260)

        self.server_input = QLineEdit()
        self.username_input = QLineEdit()

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.toggle_password_checkbox = QCheckBox("Показать пароль")
        self.toggle_password_checkbox.toggled.connect(self.toggle_password_visibility)

        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.handle_login)

        self.status_icon = QLabel("")
        self.status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("IP-адрес сервера:"))
        layout.addWidget(self.server_input)
        layout.addWidget(QLabel("Имя пользователя:"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.password_input)
        layout.addWidget(self.toggle_password_checkbox)

        layout.addWidget(self.login_button)
        layout.addWidget(self.status_icon)

        self.setLayout(layout)

        self.main_window = None
        self.main_window_factory = main_window_factory

    def toggle_password_visibility(self, checked):
        if checked:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def handle_login(self):
        server = self.server_input.text().strip()
        username = self.username_input.text().strip()
        password_str = self.password_input.text()

        if not server or not username or not password_str:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")
            return

        self.login_button.setEnabled(False)
        self.login_button.setText("Подключение...")
        self.status_icon.clear()

        try:
            socket.gethostbyname(server)
        except socket.gaierror:
            self.show_error("⛔ Невозможно разрешить адрес сервера.")
            self.reset_ui()
            return

        try:
            client = CheckpointClient(server, username, password_str)
            del password_str
            logger.info(f"Попытка входа: {username}@{server}")
            status = self.perform_login_with_timeout(client, timeout=5)

            if status == "success":
                self.show_success()
                self.launch_main_window(client)
            elif status == "timeout":
                self.show_error("⏱ Превышено время ожидания ответа от сервера.")
            elif status == "network_error":
                self.show_error("📡 Невозможно подключиться к серверу. Проверьте адрес и сеть.")
            elif status == "exception":
                self.show_error("⚠️ Ошибка при подключении. См. логи.")
            else:  # invalid
                self.show_error("🔒 Неверный логин или пароль.")

        finally:
            self.reset_ui()

    def perform_login_with_timeout(self, client, timeout=5):
        def try_login():
            return client.login()

        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(try_login)

        try:
            result = future.result(timeout=timeout)
            return "success" if result else "invalid"
        except TimeoutError:
            logger.warning("Login timeout")
            return "timeout"
        except (ConnectionError, OSError, socket.error) as e:
            logger.exception("Network/connection error")
            return "network_error"
        except Exception as e:
            logger.exception(f"Login error: {e}")
            return "exception"
        finally:
            executor.shutdown(wait=False)

    def show_error(self, message: str):
        QMessageBox.critical(self, "Ошибка подключения", message)
        self.status_icon.setText("")

    def show_success(self):
        self.status_icon.setText("✅ Успешное подключение")
        self.status_icon.setStyleSheet("color: green; font-weight: bold;")

    def reset_ui(self):
        self.login_button.setEnabled(True)
        self.login_button.setText("Войти")

    def launch_main_window(self, client):
        self.main_window = self.main_window_factory(client)
        self.main_window.show()
        self.accept()
