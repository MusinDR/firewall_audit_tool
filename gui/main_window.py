from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QTextEdit, QMessageBox, QHeaderView, QSplitter, QComboBox
)
from PyQt6.QtCore import Qt
import csv
import os

from checkpoint_client import CheckpointClient
from csv_exporter import CSVExporter
from object_resolver import ObjectResolver


class MainWindow(QMainWindow):
    def __init__(self, client: CheckpointClient):
        super().__init__()
        self.client = client
        self.setWindowTitle("CheckPoint Audit Tool")
        self.resize(1200, 800)

        self.tabs = QTabWidget()
        self.rules_tab = QWidget()
        self.audit_tab = QWidget()
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)

        self.layer_selector = QComboBox()
        self.layer_selector.setPlaceholderText("Выберите слой политики...")

        self.init_rules_tab()
        self.init_audit_tab()

        self.tabs.addTab(self.rules_tab, "Все правила")
        self.tabs.addTab(self.audit_tab, "Аудит")

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.tabs)
        splitter.addWidget(self.console_output)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(splitter)
        self.setCentralWidget(container)

        self.populate_layers()

    def init_rules_tab(self):
        layout = QVBoxLayout()

        self.load_button = QPushButton("Загрузить политики")
        self.load_button.clicked.connect(self.export_and_load_policies)

        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(10)
        self.rules_table.setHorizontalHeaderLabels([
            "Layer", "Rule #", "Name", "Source", "Destination", "Services",
            "Action", "Track", "Enabled", "Comments"
        ])
        self.rules_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.rules_table.horizontalHeader().setStretchLastSection(True)
        self.rules_table.setWordWrap(True)

        layout.addWidget(QLabel("Слой политики:"))
        layout.addWidget(self.layer_selector)
        layout.addWidget(self.load_button)
        layout.addWidget(self.rules_table)
        self.rules_tab.setLayout(layout)

    def init_audit_tab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Результаты аудита появятся здесь."))
        self.audit_tab.setLayout(layout)

    def populate_layers(self):
        try:
            self.print_log("🔍 Загружаем список слоёв политики...")
            layers_resp = self.client.client.api_call("show-access-layers", {"details-level": "standard"})
            layers = layers_resp.data.get("access-layers", [])
            self.layer_selector.clear()
            for layer in layers:
                self.layer_selector.addItem(layer["name"])
            self.print_log(f"✅ Загружено слоёв: {len(layers)}")
        except Exception as e:
            self.print_log(f"❌ Ошибка при получении слоёв: {e}")

    def export_and_load_policies(self):
        try:
            selected_layer_name = self.layer_selector.currentText()
            if not selected_layer_name:
                QMessageBox.warning(self, "Выбор слоя", "Пожалуйста, выберите слой политики.")
                return

            self.print_log(f"📦 Загружаем слой: {selected_layer_name}")

            policies, dict_objects = self.client.get_all_policies()
            all_objects = self.client.get_all_objects()

            resolver = ObjectResolver(all_objects, dict_objects)
            exporter = CSVExporter(policies, resolver)
            exporter.export_to_csv("rules_export.csv", selected_layer_name)

            self.print_log("✅ Выгрузка завершена: rules_export.csv")

            self.load_rules_from_csv("rules_export.csv")
            self.print_log("📊 Таблица правил обновлена")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить политики:\n{e}")
            self.print_log(f"❌ Ошибка при загрузке: {e}")

    def load_rules_from_csv(self, filepath: str):
        if not os.path.exists(filepath):
            self.print_log("❌ Файл не найден: " + filepath)
            return

        with open(filepath, newline='', encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            self.rules_table.setRowCount(0)
            self.rules_table.setColumnCount(len(headers))
            self.rules_table.setHorizontalHeaderLabels(headers)

            for row_idx, row_data in enumerate(reader):
                self.rules_table.insertRow(row_idx)
                for col_idx, value in enumerate(row_data):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    item.setToolTip(value)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
                    self.rules_table.setItem(row_idx, col_idx, item)

        self.rules_table.resizeRowsToContents()

    def print_log(self, message: str):
        self.console_output.append(message)
        print(message)

