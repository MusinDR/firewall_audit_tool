import csv
from object_resolver import ObjectResolver


class CSVExporter:
    def __init__(self, policies: dict, resolver: ObjectResolver):
        self.policies = policies
        self.resolver = resolver

    def export_to_csv(self, filepath: str, selected_layer: str = None):
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Заголовки CSV
            writer.writerow([
                "Layer",
                "Rule #",
                "Enabled",
                "Hits",
                "Name",
                "Source",
                "Destination",
                "Services",
                "Action",
                "Track",
                "Comments"
            ])

            if selected_layer:
                rules = self.policies.get(selected_layer)
                if not rules:
                    print(f"❌ Слой '{selected_layer}' не найден.")
                    return
                self._write_rules(writer, rules, selected_layer)
            else:
                for layer_name, rules in self.policies.items():
                    self._write_rules(writer, rules, layer_name)

    def _write_rules(self, writer, rules, layer_name, parent_prefix="", display_layer=None):
        display_layer = display_layer or layer_name

        for index, rule in enumerate(rules, start=1):
            rule_num = f"{parent_prefix}{index}"

            # Получаем track.type с учётом разных возможных типов
            track = rule.get("track")
            track_type = track.get("type") if isinstance(track, dict) else track

            writer.writerow([
                display_layer,
                rule_num,
                rule.get("enabled"),
                rule.get("hits").get("value"),
                rule.get("name", ""),
                self._format_uids(rule.get("source")),
                self._format_uids(rule.get("destination")),
                self._format_uids(rule.get("service")),
                self._format_uid(rule.get("action")),
                self._format_uid(track_type),
                str(rule.get("comments") or "")
            ])

            # Обработка inline-layer (вложенные правила)
            if "inline-layer" in rule:
                nested_layer_uid = rule["inline-layer"]
                nested_layer_name = self.resolver.get_layer_name_by_uid(nested_layer_uid)
                nested_rules = self.policies.get(nested_layer_name)

                if nested_rules:
                    self._write_rules(
                        writer,
                        nested_rules,
                        layer_name=layer_name,  # сохраняем текущий контекст
                        parent_prefix=f"{rule_num}.",
                        display_layer=nested_layer_name  # отображаем имя вложенного слоя
                    )
                else:
                    writer.writerow([
                        nested_layer_name or nested_layer_uid,
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
