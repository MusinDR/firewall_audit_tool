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
                "Section",
                "Rule #",
                "Enabled",
                "Hits",
                "Name",
                "Source",
                "Destination",
                "Services",
                "Action",
                "Time",
                "Track",
                "Install On",
                "Comments"
            ])

            if selected_layer:
                rules = self.policies.get(selected_layer)
                if not rules:
                    print(f"❌ Слой '{selected_layer}' не найден.")
                    return
                self._write_rules(writer, rules, selected_layer, layer_path=[selected_layer])
            else:
                for layer_name, rules in self.policies.items():
                    self._write_rules(writer, rules, layer_name, layer_path=[layer_name])

    def _write_rules(self, writer, rules, layer_name, parent_prefix="", layer_path=None, section_name=""):
        if layer_path is None:
            layer_path = [layer_name]
        rule_index = 0

        for rule in rules:
            if rule.get("type") == "access-section":
                rule_index += 1
                rule_num = f"{parent_prefix}{rule_index}"
                current_section = rule.get("name", "[Без имени]")

                self._write_rules(
                    writer,
                    rule.get("rulebase", []),
                    layer_name=layer_name,
                    parent_prefix=f"{rule_num}.",
                    layer_path=layer_path,
                    section_name=current_section
                )
                continue

            rule_index += 1
            rule_num = f"{parent_prefix}{rule_index}"

            track = rule.get("track")
            track_type = track.get("type") if isinstance(track, dict) else track

            writer.writerow([
                " / ".join(layer_path),
                section_name,
                rule_num,
                rule.get("enabled"),
                rule.get("hits", {}).get("value"),
                rule.get("name", ""),
                self._format_uids(rule.get("source")),
                self._format_uids(rule.get("destination")),
                self._format_uids(rule.get("service")),
                self._format_uid(rule.get("action")),
                self._format_uids(rule.get("time")),
                self._format_uid(track_type),
                self._format_uids(rule.get("install-on")),
                str(rule.get("comments") or "")
            ])

            if "inline-layer" in rule:
                nested_layer_uid = rule["inline-layer"]
                nested_layer_name = self.resolver.get_layer_name_by_uid(nested_layer_uid)
                nested_rules = self.policies.get(nested_layer_name)

                if nested_rules:
                    self._write_rules(
                        writer,
                        nested_rules,
                        layer_name=layer_name,
                        parent_prefix=f"{rule_num}.",
                        layer_path=layer_path + [nested_layer_name],
                        section_name=section_name
                    )
                else:
                    writer.writerow([
                        nested_layer_name or nested_layer_uid,
                        section_name,
                        f"{rule_num}.x",
                        "[Ошибка: нет данных для inline-layer]",
                        "", "", "", "", "", "", "", "", ""
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
