# gui/audit/audit_settings_dialog.py

from PyQt6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QVBoxLayout


class AuditSettingsDialog(QDialog):
    def __init__(self, current_settings: dict):
        super().__init__()
        self.setWindowTitle("Настройки аудита")
        self.resize(300, 250)

        self.checks = {
            "any_to_any_accept": QCheckBox("Any / Any → Accept"),
            "no_track": QCheckBox("No Track configured"),
            "hit_count_zero": QCheckBox("Hit count is zero"),
            "disabled_rule": QCheckBox("Rule is disabled"),
            "any_service_accept": QCheckBox("Service is Any"),
            "any_destination_accept": QCheckBox("Destination is Any"),
            "any_source_accept": QCheckBox("Source is Any"),
        }

        layout = QVBoxLayout()
        for key, checkbox in self.checks.items():
            checkbox.setChecked(current_settings.get(key, True))
            layout.addWidget(checkbox)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)
        self.setLayout(layout)

    def get_selected_checks(self) -> dict:
        return {key: checkbox.isChecked() for key, checkbox in self.checks.items()}
