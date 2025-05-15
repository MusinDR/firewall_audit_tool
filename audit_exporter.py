import csv
from collections import defaultdict

SEVERITY_ORDER = {
    "Critical": 4,
    "High": 3,
    "Medium": 2,
    "Info": 1
}

class AuditExporter:

    SEVERITY_ICONS = {
        "Critical": "🔴",
        "High": "🟠",
        "Medium": "🟡",
        "Info": "🔵"
    }

    def __init__(self, findings: list[dict]):
        self.findings = findings

    def export_to_csv(self, filepath: str):
        grouped = defaultdict(list)

        # Группируем по UID
        for finding in self.findings:
            uid = finding["rule_uid"]
            grouped[uid].append(finding)

        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Severity",
                "Issues",
                "Layer",
                "Rule #",
                "Rule Name",
                "Source",
                "Destination",
                "Service",
                "Action",
                "Track",
                "Enabled",
                "Comments"
            ])

            for uid, issues in grouped.items():
                rule_data = issues[0]["rule"]
                max_severity = self._get_max_severity([i["severity"] for i in issues])
                display_severity = f"{self.SEVERITY_ICONS.get(max_severity)} {max_severity}"
                issues_joined = "; ".join(sorted(set(i["issue"] for i in issues)))

                writer.writerow([
                    display_severity,
                    issues_joined,
                    issues[0]["layer"],
                    issues[0]["rule_number"],
                    issues[0]["rule_name"],
                    rule_data.get("source", ""),
                    rule_data.get("destination", ""),
                    rule_data.get("service", ""),
                    rule_data.get("action", ""),
                    rule_data.get("track", ""),
                    rule_data.get("enabled", ""),
                    rule_data.get("comments", "")
                ])

    def _get_max_severity(self, severities: list[str]) -> str:
        return max(severities, key=lambda s: SEVERITY_ORDER.get(s, 0))
