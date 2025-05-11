import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QTableView, QSplitter, QMessageBox, QDialog, QFormLayout,
    QLineEdit, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem
import json
from checkpoint_client import CheckpointClient
from object_resolver import ObjectResolver
from csv_exporter import CSVExporter
from audit_engine import RuleAuditor


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


class MainWindow(QMainWindow):
    def __init__(self, client: CheckpointClient):
        super().__init__()
        self.setWindowTitle("Firewall Audit Tool")
        self.resize(1000, 600)
        self.client = client

        self.tabs = QTabWidget()
        self.rules_tab = QWidget()
        self.audit_tab = QWidget()
        self.tabs.addTab(self.rules_tab, "Все правила")
        self.tabs.addTab(self.audit_tab, "Результаты аудита")
        self.setCentralWidget(self.tabs)

        self.rules_table = QTableView()
        self.rules_model = QStandardItemModel()
        self.rules_table.setModel(self.rules_model)

        self.rules_layout = QVBoxLayout()
        self.rules_layout.addWidget(self.rules_table)
        self.rules_tab.setLayout(self.rules_layout)

        self.load_data()

    def load_data(self):
        policies, objects_dict = self.client.get_all_policies()
        all_objects = self.client.get_all_objects()
        resolver = ObjectResolver(all_objects, objects_dict)

        # Объединяем все правила в плоский список
        exporter = CSVExporter(policies, resolver)
        flat_rules = exporter.flatten_rules()

        headers = ["Layer", "Rule #", "Name", "Source", "Destination", "Services", "Action", "Track", "Enabled", "Comments"]
        self.rules_model.setHorizontalHeaderLabels(headers)
        for row in flat_rules:
            items = [QStandardItem(str(row.get(col, ""))) for col in headers]
            self.rules_model.appendRow(items)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    login = LoginDialog()
    if login.exec() == QDialog.DialogCode.Accepted:
        ip, user, passwd = login.get_credentials()
        client = CheckpointClient(ip, user, passwd)

        if client.login():
            window = MainWindow(client)
            window.show()
            app.exec()
            client.logout()
        else:
            QMessageBox.critical(None, "Ошибка", "Не удалось выполнить вход. Проверьте данные.")
            sys.exit(1)
    else:
        sys.exit(0)
