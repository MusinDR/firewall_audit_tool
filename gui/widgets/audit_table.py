# gui/widgets/audit_table.py

from PyQt6.QtWidgets import QTableWidget, QHeaderView

def create_audit_table() -> QTableWidget:
    table = QTableWidget()
    table.setColumnCount(6)
    table.setHorizontalHeaderLabels([
        "Layer", "Rule #", "Rule Name", "Severity", "Issue", "Comment"
    ])
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    table.setWordWrap(True)
    return table
