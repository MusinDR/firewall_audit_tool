import csv
from object_resolver import ObjectResolver


class CSVExporter:
    def __init__(self, policies: dict, resolver: ObjectResolver):
        self.policies = policies
        self.resolver = resolver

    def export_to_csv(self, filepath: str):
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Заголовки CSV
            writer.writerow([
                "Layer",
                "Rule #",
                "Name",
                "Source",
                "Destination",
                "Services",
                "Action",
                "Track",
                "Enabled",
                "Comments"
            ])

            for layer_name, rules in self.policies.items():
                self._write_rules(writer, rules, layer_name)

    def _write_rules(self, writer, rules, layer_name, parent_prefix=""):
        for index, rule in enumerate(rules, start=1):
            rule_num = f"{parent_prefix}{index}"

            writer.writerow([
                layer_name,
                rule_num,
                rule.get("name"),
                self._format_uids(rule.get("source")),
                self._format_uids(rule.get("destination")),
                self._format_uids(rule.get("service")),
                self._format_uid(rule.get("action")),
                self._format_uid((rule.get("track") or {}).get("type")),
                rule.get("enabled"),
                rule.get("comments")
            ])

            # рекурсивно обрабатываем inline-layer
            if "inline-layer" in rule:
                nested_layer_uid = rule["inline-layer"]
                layer_name = self.resolver.get_layer_name_by_uid(nested_layer_uid)
                nested_rules = self.policies.get(layer_name)
                if nested_rules:
                    self._write_rules(writer, nested_rules, nested_layer_uid, parent_prefix=f"{rule_num}.")
                else:
                    writer.writerow([
                        nested_layer_uid,
                        f"{rule_num}.x",
                        "[Ошибка: нет данных для inline-layer]",
                        "", "", "", "", "", "", ""
                    ])

    def _format_uids(self, items: list) -> str:
        if not items:
            return ""
        return "; ".join([
            self.resolver.format(obj.get("uid") if isinstance(obj, dict) else obj)
            for obj in items
        ])

    def _format_uid(self, item) -> str:
        if isinstance(item, dict):
            return self.resolver.format(item.get("uid"))
        if isinstance(item, str):
            return self.resolver.format(item)
        return "[Invalid UID]"
