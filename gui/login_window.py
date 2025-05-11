from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Авторизация")
        self.resize(300, 150)
        layout = QFormLayout(self)

        self.ip_input = QLineEdit(self)
        self.user_input = QLineEdit(self)
        self.pass_input = QLineEdit(self)
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addRow("IP-адрес:", self.ip_input)
        layout.addRow("Пользователь:", self.user_input)
        layout.addRow("Пароль:", self.pass_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_credentials(self):
        return self.ip_input.text(), self.user_input.text(), self.pass_input.text()
