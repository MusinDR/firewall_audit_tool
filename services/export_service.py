# services/export_service.py

import csv
import shutil


class ExportService:
    def export_table_to_csv(self, table_widget, path: str):
        with open(path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            headers = [
                table_widget.horizontalHeaderItem(i).text()
                for i in range(table_widget.columnCount())
            ]
            writer.writerow(headers)
            for row in range(table_widget.rowCount()):
                row_data = [
                    table_widget.item(row, col).text() if table_widget.item(row, col) else ""
                    for col in range(table_widget.columnCount())
                ]
                writer.writerow(row_data)

    def copy_csv_file(self, src: str, dst: str):
        shutil.copyfile(src, dst)
