# core/csv_exporter.py

import csv

from core.rule_formatter import RuleFormatter
from resolvers.object_resolver import ObjectResolver


class CSVExporter:
    def __init__(self, policies: dict, resolver: ObjectResolver):
        self.policies = policies
        self.formatter = RuleFormatter(resolver)

    def export_to_csv(self, filepath: str, selected_layer: str = None):
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
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
                    "Comments",
                ]
            )

            layers = [selected_layer] if selected_layer else list(self.policies.keys())
            for layer in layers:
                rules = self.policies.get(layer)
                if not rules:
                    continue
                self._process_rules(
                    writer,
                    rules=rules,
                    layer_name=layer,
                    layer_path=[layer],
                    parent_prefix="",
                    rule_counter=[0],
                    section_name="",
                )

    def _process_rules(
        self, writer, rules, layer_name, layer_path, parent_prefix, rule_counter, section_name
    ):
        for rule in rules:
            rule_type = rule.get("type", "access-rule")

            if rule_type == "access-section":
                self._process_rules(
                    writer,
                    rule.get("rulebase", []),
                    layer_name=layer_name,
                    layer_path=layer_path,
                    parent_prefix=parent_prefix,
                    rule_counter=rule_counter,
                    section_name=rule.get("name", "[Без имени]"),
                )
                continue

            rule_counter[0] += 1
            rule_number = f"{parent_prefix}{rule_counter[0]}"
            writer.writerow(self.formatter.format(rule, rule_number, section_name, layer_path))

            if "inline-layer" in rule:
                nested_uid = rule["inline-layer"]
                nested_layer_name = self.formatter.resolver.get_layer_name_by_uid(nested_uid)
                nested_rules = self.policies.get(nested_layer_name)
                if nested_rules:
                    self._process_rules(
                        writer,
                        nested_rules,
                        layer_name=nested_layer_name,
                        layer_path=layer_path + [nested_layer_name],
                        parent_prefix=f"{rule_number}.",
                        rule_counter=[0],  # новая локальная вложенность
                        section_name=section_name,
                    )
                else:
                    writer.writerow(
                        [
                            nested_layer_name or nested_uid,
                            section_name,
                            f"{rule_number}.x",
                            "[Ошибка: нет данных для inline-layer]",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ]
                    )
