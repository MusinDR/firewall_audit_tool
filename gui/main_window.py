from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QTextEdit, QMessageBox, QHeaderView, QSplitter, QComboBox, QFileDialog
)
from PyQt6.QtCore import Qt
import csv
import os
import json

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
        self.export_button.setFixedHeight(28)
        self.export_button.setMaximumWidth(150)

        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(10)
        self.rules_table.setHorizontalHeaderLabels([
            "Layer", "Rule #", "Name", "Source", "Destination", "Services",
            "Action", "Track", "Enabled", "Comments"
        ])
        self.rules_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.rules_table.horizontalHeader().setStretchLastSection(True)
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
        layout.addWidget(QLabel("Результаты аудита появятся здесь."))
        self.audit_tab.setLayout(layout)

    def fetch_from_firewall(self):
        try:
            self.print_log("📡 Выгружаем политики и объекты с МЭ...")
            policies, dict_objects = self.client.get_all_policies()
            all_objects = self.client.get_all_objects()

            with open("policies.json", "w", encoding="utf-8") as f:
                json.dump(policies, f, indent=2, ensure_ascii=False)
            with open("objects-dictionary.json", "w", encoding="utf-8") as f:
                json.dump(dict_objects, f, indent=2, ensure_ascii=False)
            with open("all_objects.json", "w", encoding="utf-8") as f:
                json.dump(all_objects, f, indent=2, ensure_ascii=False)

            self.print_log("✅ Данные успешно выгружены")
            self.populate_layers()

            # Активируем действия
            self.load_button.setEnabled(True)
            self.export_button.setEnabled(True)

        except Exception as e:
            self.print_log(f"❌ Ошибка при выгрузке: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при выгрузке с МЭ:\n{e}")

    def populate_layers(self):
        try:
            if not os.path.exists("policies.json"):
                self.print_log("❗ Сначала необходимо выгрузить политики с МЭ")
                return
            with open("policies.json", encoding="utf-8") as f:
                policies = json.load(f)
            self.layer_selector.clear()
            for layer_name in policies.keys():
                self.layer_selector.addItem(layer_name)
            self.print_log("✅ Слои загружены из policies.json")
        except Exception as e:
            self.print_log(f"❌ Ошибка при загрузке слоёв: {e}")

    def export_and_load_selected_layer(self):
        try:
            selected_layer_name = self.layer_selector.currentText()
            if not selected_layer_name:
                QMessageBox.warning(self, "Выбор слоя", "Пожалуйста, выберите слой политики.")
                return

            with open("policies.json", encoding="utf-8") as f:
                policies = json.load(f)
            with open("objects-dictionary.json", encoding="utf-8") as f:
                dict_objects = json.load(f)
            with open("all_objects.json", encoding="utf-8") as f:
                all_objects = json.load(f)

            resolver = ObjectResolver(all_objects, dict_objects)
            exporter = CSVExporter(policies, resolver)
            exporter.export_to_csv("rules_export.csv", selected_layer_name)

            self.load_rules_from_csv("rules_export.csv")
            self.print_log(f"📊 Таблица правил обновлена для слоя: {selected_layer_name}")
        except Exception as e:
            self.print_log(f"❌ Ошибка при отображении слоя: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при отображении:\n{e}")

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

    def export_table_to_csv(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Сохранить как CSV", "", "CSV Files (*.csv)")
        if not filepath:
            return

        try:
            with open(filepath, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                headers = [self.rules_table.horizontalHeaderItem(i).text() for i in range(self.rules_table.columnCount())]
                writer.writerow(headers)
                for row in range(self.rules_table.rowCount()):
                    row_data = [
                        self.rules_table.item(row, col).text() if self.rules_table.item(row, col) else ""
                        for col in range(self.rules_table.columnCount())
                    ]
                    writer.writerow(row_data)

            self.print_log(f"✅ Таблица экспортирована в {filepath}")
        except Exception as e:
            self.print_log(f"❌ Ошибка при экспорте: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при экспорте в CSV:\n{e}")

    def print_log(self, message: str):
        self.console_output.append(message)
        print(message)
