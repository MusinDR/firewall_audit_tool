# main_window.py


import csv
import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QHBoxLayout, QHeaderView, QLabel,
    QMainWindow, QMessageBox, QPushButton, QSplitter, QTableWidget,
    QTableWidgetItem, QTabWidget, QTextEdit, QVBoxLayout, QWidget
)

from infrastructure.checkpoint_api_client import CheckpointClient
from infrastructure.logger import logger
from gui.audit.audit_settings_dialog import AuditSettingsDialog
from services import AuditService, FetchService, PolicyService
from gui.rules.rules_table import create_rules_table
from gui.audit.audit_table import create_audit_table
from gui.utils.table_to_csv_exporter import TableExporterCSV
from gui.utils.table_from_csv_loader import load_table_from_csv


class MainWindow(QMainWindow):
    def __init__(self, client: CheckpointClient):
        super().__init__()
        self.client = client
        self.setWindowTitle("CheckPoint Audit Tool")
        self.resize(1200, 800)

        self.audit_service = AuditService(log_func=self.print_log)
        self.policy_service = PolicyService()

        self.audit_checks = {
            'any_to_any_accept': True,
            'no_track': True,
            'hit_count_zero': True,
            'disabled_rule': True,
            'any_service_accept': True,
            'any_destination_accept': True,
            'any_source_accept': True,
        }

        self.tabs = QTabWidget()
        self.rules_tab = QWidget()
        self.audit_tab = QWidget()
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)

        self.layer_selector = QComboBox()
        self.layer_selector.setPlaceholderText("Выберите слой политики...")

        self.audit_layer_selector = QComboBox()
        self.audit_layer_selector.setPlaceholderText("Выберите слой для аудита...")

        self.init_rules_tab()
        self.init_audit_tab()

        self.tabs.addTab(self.rules_tab, "Все правила")
        self.tabs.addTab(self.audit_tab, "Аудит")

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.tabs)
        splitter.addWidget(self.console_output)

        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        container.setLayout(layout)
        self.setCentralWidget(container)

    def init_rules_tab(self):
        layout = QVBoxLayout()

        self.fetch_button = QPushButton("📥 Выгрузить политики с МЭ")
        self.fetch_button.clicked.connect(self.fetch_from_firewall)

        self.load_button = QPushButton("📊 Показать слой")
        self.load_button.clicked.connect(self.export_and_load_selected_layer)
        self.load_button.setEnabled(False)

        self.export_button = QPushButton("💾 Экспорт в CSV...")
        self.export_button.clicked.connect(self.export_rules_table)
        self.export_button.setEnabled(False)

        self.rules_table = create_rules_table()

        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Слой политики:"))
        control_layout.addWidget(self.layer_selector)
        control_layout.addWidget(self.load_button)
        control_layout.addStretch()

        layout.addWidget(self.fetch_button)
        layout.addLayout(control_layout)
        layout.addWidget(self.rules_table)

        export_layout = QHBoxLayout()
        export_layout.addStretch()
        export_layout.addWidget(self.export_button)
        layout.addLayout(export_layout)

        self.rules_tab.setLayout(layout)

    def init_audit_tab(self):
        layout = QVBoxLayout()

        self.audit_button = QPushButton("🔍 Выполнить аудит")
        self.audit_button.clicked.connect(self.run_audit)

        self.settings_button = QPushButton("⚙ Настройки аудита")
        self.settings_button.clicked.connect(self.open_audit_settings)

        self.export_audit_button = QPushButton("💾 Экспорт аудита в CSV")
        self.export_audit_button.clicked.connect(self.export_audit_table)
        self.export_audit_button.setEnabled(False)

        audit_controls = QHBoxLayout()
        audit_controls.addWidget(QLabel("Слой для аудита:"))
        audit_controls.addWidget(self.audit_layer_selector)
        audit_controls.addWidget(self.audit_button)
        audit_controls.addWidget(self.settings_button)
        audit_controls.addWidget(self.export_audit_button)

        self.audit_table = create_audit_table()

        layout.addLayout(audit_controls)
        layout.addWidget(self.audit_table)
        self.audit_tab.setLayout(layout)

    def run_audit(self):
        layer = self.audit_layer_selector.currentText()
        if not layer:
            QMessageBox.warning(self, "Ошибка", "Выберите слой.")
            return
        try:
            findings, summary = self.audit_service.audit_layer(layer, self.audit_checks)

            if not findings:
                QMessageBox.information(self, "Аудит завершен", "Нарушений не найдено.")
                return

            self.audit_service.export_findings(findings, "tmp/audit_findings.csv")
            load_table_from_csv(self.audit_table, "tmp/audit_findings.csv", self.print_log)
            self.export_audit_button.setEnabled(True)

        except Exception as e:
            self.print_log(f"❌ Ошибка аудита: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))

    def open_audit_settings(self):
        dialog = AuditSettingsDialog(self.audit_checks)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.audit_checks = dialog.get_selected_checks()
            self.print_log("⚙ Настройки аудита обновлены")

    def fetch_from_firewall(self):
        try:
            self.print_log("🚀 Запуск выгрузки в фоне...")
            self.fetch_button.setEnabled(False)

            self.fetch_service = FetchService(
                client=self.client,
                policy_service=self.policy_service,
                on_progress=self.print_log,
                on_result=self.handle_fetch_success,
                on_error=self.handle_fetch_error,
            )
            self.fetch_service.start()

        except Exception as e:
            self.print_log(f"❌ Ошибка при выгрузке: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))

    def handle_fetch_success(self):
        self.populate_layers()
        self.load_button.setEnabled(True)
        self.export_button.setEnabled(True)
        self.fetch_button.setEnabled(True)
        self.print_log("✅ Данные сохранены и загружены")

    def handle_fetch_error(self, message: str):
        self.print_log(message)
        QMessageBox.critical(self, "Ошибка", message)
        self.fetch_button.setEnabled(True)

    def handle_fetch_result(self, policies, dict_objects, all_objects):
        try:
            self.policy_service.save_policies(policies, dict_objects, all_objects)
            self.populate_layers()
            self.load_button.setEnabled(True)
            self.export_button.setEnabled(True)
            self.fetch_button.setEnabled(True)
            self.print_log("✅ Данные сохранены и загружены")
        except Exception as e:
            self.print_log(f"❌ Ошибка при сохранении: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))

    def populate_layers(self):
        try:
            layers = self.policy_service.get_policy_layers()
            self.layer_selector.clear()
            self.audit_layer_selector.clear()
            for layer in layers:
                self.layer_selector.addItem(layer)
                self.audit_layer_selector.addItem(layer)
            self.print_log("✅ Слои загружены")
        except Exception as e:
            self.print_log(f"❌ Ошибка загрузки слоёв: {e}")

    def export_and_load_selected_layer(self):
        layer = self.layer_selector.currentText()
        if not layer:
            QMessageBox.warning(self, "Ошибка", "Выберите слой.")
            return
        try:
            self.policy_service.export_layer(layer, "tmp/rules_export.csv")
            load_table_from_csv(self.rules_table, "tmp/rules_export.csv", self.print_log)
        except Exception as e:
            self.print_log(f"❌ Ошибка отображения: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))


    def export_table_to_csv(self, table_widget: QTableWidget, dialog_title: str = "Сохранить как CSV"):
        path, _ = QFileDialog.getSaveFileName(self, dialog_title, "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            TableExporterCSV(table_widget, path).export()
            self.print_log(f"✅ Таблица экспортирована в {path}")
        except Exception as e:
            self.print_log(f"❌ Ошибка при экспорте: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))

    def export_rules_table(self):
        self.export_table_to_csv(self.rules_table, "Сохранить таблицу правил")

    def export_audit_table(self):
        self.export_table_to_csv(self.audit_table, "Сохранить отчёт об аудите")

    def print_log(self, message: str, level="info"):
        if level == "debug":
            logger.debug(message)
        elif level == "warning":
            logger.warning(message)
        elif level == "error":
            logger.error(message)
        else:
            logger.info(message)
        self.console_output.append(message)
