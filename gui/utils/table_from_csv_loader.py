# gui/utils/table_from_csv_loader.py

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
import os
import csv

def load_table_from_csv(table: QTableWidget, path: str, print_log=None):
    if not os.path.exists(path):
        if print_log:
            print_log(f"❌ Файл не найден: {path}")
        return

    with open(path, newline='', encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        table.setRowCount(0)
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        for i, row in enumerate(reader):
            table.insertRow(i)
            for j, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                item.setToolTip(val)
                table.setItem(i, j, item)

    table.resizeRowsToContents()
