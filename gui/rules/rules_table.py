# gui/rules/rules_table.py

from PyQt6.QtWidgets import QHeaderView, QTableWidget


def create_rules_table() -> QTableWidget:
    table = QTableWidget()
    table.setColumnCount(10)
    table.setHorizontalHeaderLabels(
        [
            "Layer",
            "Rule #",
            "Name",
            "Source",
            "Destination",
            "Services",
            "Action",
            "Track",
            "Enabled",
            "Comments",
        ]
    )
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    table.setWordWrap(True)
    return table
