from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel, QTextEdit,
    QMessageBox, QHeaderView, QSplitter, QComboBox, QFileDialog, QDialog
)
from PyQt6.QtCore import Qt, QThread
import csv
import os

from checkpoint_client import CheckpointClient
from fetch_worker import FetchWorker
from gui.audit_settings_dialog import AuditSettingsDialog
from core.policy_controller import export_selected_layer_to_csv
from core.audit_controller import run_audit_and_export
from core.data_loader import load_json
from core.data_writer import save_all
from core.logger import logger


class MainWindow(QMainWindow):
    def __init__(self, client: CheckpointClient):
        super().__init__()
        self.client = client
        self.setWindowTitle("CheckPoint Audit Tool")
        self.resize(1200, 800)

        self.audit_checks = {
            'any_to_any_accept': True,
            'no_track': True,
            'hit_count_zero': True,
            'disabled_rule': True,
            'any_service_accept': True,
            'any_destination_accept': True,
            'any_source_accept': True
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
        self.export_button.clicked.connect(self.export_table_to_csv)
        self.export_button.setEnabled(False)

        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(10)
        self.rules_table.setHorizontalHeaderLabels([
            "Layer", "Rule #", "Name", "Source", "Destination", "Services",
            "Action", "Track", "Enabled", "Comments"
        ])
        self.rules_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.rules_table.setWordWrap(True)

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
        self.export_audit_button.clicked.connect(self.export_audit_findings)
        self.export_audit_button.setEnabled(False)

        audit_controls = QHBoxLayout()
        audit_controls.addWidget(QLabel("Слой для аудита:"))
        audit_controls.addWidget(self.audit_layer_selector)
        audit_controls.addWidget(self.audit_button)
        audit_controls.addWidget(self.settings_button)
        audit_controls.addWidget(self.export_audit_button)

        self.audit_table = QTableWidget()
        self.audit_table.setColumnCount(6)
        self.audit_table.setHorizontalHeaderLabels([
            "Layer", "Rule #", "Rule Name", "Severity", "Issue", "Comment"
        ])
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.audit_table.setWordWrap(True)

        layout.addLayout(audit_controls)
        layout.addWidget(self.audit_table)
        self.audit_tab.setLayout(layout)

    def run_audit(self):
        layer = self.audit_layer_selector.currentText()
        if not layer:
            QMessageBox.warning(self, "Ошибка", "Выберите слой.")
            return
        try:
            from audit.audit_engine import RuleAuditor
            from resolvers.object_resolver import ObjectResolver
            from core.data_loader import load_all_data

            policies, dict_objects, all_objects = load_all_data()
            resolver = ObjectResolver(all_objects, dict_objects)
            auditor = RuleAuditor(policies, resolver, enabled_checks=self.audit_checks, log_func=self.print_log)
            findings, summary = auditor.run_audit(selected_layer=layer)

            if not findings:
                QMessageBox.information(self, "Аудит завершен", "Нарушений не найдено.")
                return

            from core.audit_controller import export_findings_to_csv
            export_findings_to_csv(findings, "tmp/audit_findings.csv")
            self.load_audit_findings()
            self.export_audit_button.setEnabled(True)
            self.print_log(f"\n✅ Аудит завершён. Найдено: {len(findings)} нарушений.")
            #self.print_log(summary)

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
            self.thread = QThread()
            self.worker = FetchWorker(self.client)
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)

            self.worker.progress.connect(self.print_log)
            self.worker.error.connect(lambda msg: QMessageBox.critical(self, "Ошибка", msg))
            self.worker.result.connect(self.handle_fetch_result)

            self.thread.start()
            self.fetch_button.setEnabled(False)
        except Exception as e:
            self.print_log(f"❌ Ошибка при выгрузке: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))

    def handle_fetch_result(self, policies, dict_objects, all_objects):
        try:
            save_all(policies, dict_objects, all_objects)
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
            policies = load_json("tmp/policies.json")
            self.layer_selector.clear()
            self.audit_layer_selector.clear()
            for layer in policies:
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
            export_selected_layer_to_csv(layer)
            self.load_rules_from_csv("tmp/rules_export.csv")
            self.print_log(f"📋 Правила слоя '{layer}' загружены.")
        except Exception as e:
            self.print_log(f"❌ Ошибка отображения: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))

    def load_rules_from_csv(self, path: str):
        if not os.path.exists(path):
            self.print_log(f"❌ Файл не найден: {path}")
            return

        with open(path, newline='', encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            self.rules_table.setRowCount(0)
            self.rules_table.setColumnCount(len(headers))
            self.rules_table.setHorizontalHeaderLabels(headers)

            for i, row in enumerate(reader):
                self.rules_table.insertRow(i)
                for j, val in enumerate(row):
                    item = QTableWidgetItem(val)
                    item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    item.setToolTip(val)
                    self.rules_table.setItem(i, j, item)

        self.rules_table.resizeRowsToContents()

    def load_audit_findings(self):
        path = "tmp/audit_findings.csv"
        if not os.path.exists(path):
            self.print_log("❌ Файл аудита не найден.")
            return

        with open(path, newline='', encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            self.audit_table.setRowCount(0)
            self.audit_table.setColumnCount(len(headers))
            self.audit_table.setHorizontalHeaderLabels(headers)

            for i, row in enumerate(reader):
                self.audit_table.insertRow(i)
                for j, val in enumerate(row):
                    item = QTableWidgetItem(val)
                    item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    item.setToolTip(val)
                    self.audit_table.setItem(i, j, item)

        self.audit_table.resizeRowsToContents()

    def export_table_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить как CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            with open(path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                headers = [self.rules_table.horizontalHeaderItem(i).text() for i in range(self.rules_table.columnCount())]
                writer.writerow(headers)
                for row in range(self.rules_table.rowCount()):
                    row_data = [
                        self.rules_table.item(row, col).text() if self.rules_table.item(row, col) else ""
                        for col in range(self.rules_table.columnCount())
                    ]
                    writer.writerow(row_data)
            self.print_log(f"✅ Таблица экспортирована в {path}")
        except Exception as e:
            self.print_log(f"❌ Ошибка при экспорте: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))

    def export_audit_findings(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить отчёт об аудите", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            with open("tmp/audit_findings.csv", encoding="utf-8") as src, open(path, "w", newline='', encoding="utf-8") as dst:
                for line in src:
                    dst.write(line)
            self.print_log(f"✅ Аудит экспортирован в {path}")
        except Exception as e:
            self.print_log(f"❌ Ошибка экспорта аудита: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))

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

