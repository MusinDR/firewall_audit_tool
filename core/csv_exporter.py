from resolvers.object_resolver import ObjectResolver
from core.rule_formatter import RuleFormatter
import csv


class CSVExporter:
    def __init__(self, policies: dict, resolver: ObjectResolver):
        self.policies = policies
        self.formatter = RuleFormatter(resolver)

    def export_to_csv(self, filepath: str, selected_layer: str = None):
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Layer", "Section", "Rule #", "Enabled", "Hits", "Name",
                "Source", "Destination", "Services", "Action", "Time",
                "Track", "Install On", "Comments"
            ])

            if selected_layer:
                rules = self.policies.get(selected_layer)
                if not rules:
                    print(f"❌ Слой '{selected_layer}' не найден.")
                    return
                self._write_rules(writer, rules, layer_name=selected_layer, layer_path=[selected_layer])
            else:
                for layer_name, rules in self.policies.items():
                    self._write_rules(writer, rules, layer_name=layer_name, layer_path=[layer_name])

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

            writer.writerow(
                self.formatter.format(rule, rule_num, section_name, layer_path)
            )

            if "inline-layer" in rule:
                nested_uid = rule["inline-layer"]
                nested_layer_name = self.formatter.resolver.get_layer_name_by_uid(nested_uid)
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
                        nested_layer_name or nested_uid,
                        section_name,
                        f"{rule_num}.x",
                        "[Ошибка: нет данных для inline-layer]",
                        "", "", "", "", "", "", "", "", ""
                    ])
