# gui/widgets/table_to_csv_exporter.py

import csv


class TableExporterCSV:
    def __init__(self, table_widget, path: str):
        self.table_widget = table_widget
        self.path = path

    def export(self) -> None:
        column_count = self.table_widget.columnCount()
        row_count = self.table_widget.rowCount()

        with open(self.path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            headers = [
                self.table_widget.horizontalHeaderItem(i).text()
                for i in range(column_count)
            ]
            writer.writerow(headers)

            for row in range(row_count):
                row_data = [
                    self.table_widget.item(row, col).text()
                    if self.table_widget.item(row, col) else ""
                    for col in range(column_count)
                ]
                writer.writerow(row_data)
