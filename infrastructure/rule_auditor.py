# infrastructure/rule_auditor.py

from collections import Counter

from infrastructure.rule_formatter import RuleFormatter


class RuleAuditor:
    DEFAULT_CHECKS = {
        "any_to_any_accept": True,
        "no_track": True,
        "hit_count_zero": True,
        "disabled_rule": True,
        "any_service_accept": True,
        "any_destination_accept": True,
        "any_source_accept": True,
    }

    SEVERITY_ICONS = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Info": "🔵"}

    def __init__(self, policies: dict, resolver, enabled_checks: dict = None, log_func=print):
        self.policies = policies
        self.resolver = resolver
        self.formatter = RuleFormatter(resolver)
        self.enabled_checks = enabled_checks or self.DEFAULT_CHECKS
        self.findings = []
        self.log = log_func

    def run_audit(self, selected_layer: str = None) -> tuple[list[dict], str]:
        self.log("\n=======================================\n")
        self.log("\n🚀 Запуск аудита...")
        self.findings.clear()

        layers = [selected_layer] if selected_layer else list(self.policies.keys())
        for layer in layers:
            rules = self.policies.get(layer)
            if not rules:
                continue
            rule_count = self._count_access_rules(rules)
            self.log(f"🔍 Слой: {layer} ({rule_count} правил)")
            self._process_rules(rules, layer_path=[layer])
        summary = self._build_summary()
        self.log(summary)
        return self.findings, summary

    def _count_access_rules(self, rules) -> int:
        count = 0
        for rule in rules:
            if rule.get("type") == "access-rule":
                count += 1
            elif rule.get("type") == "access-section":
                count += self._count_access_rules(rule.get("rulebase", []))
        return count

    def _process_rules(
        self, rules, layer_path, parent_prefix="", rule_counter=None, section_name=""
    ):
        if rule_counter is None:
            rule_counter = [0]

        for rule in rules:
            rule_type = rule.get("type", "access-rule")
            rule_name = rule.get("name", "")

            if rule_type == "access-section":
                self._process_rules(
                    rule.get("rulebase", []),
                    layer_path,
                    parent_prefix,
                    rule_counter,
                    rule.get("name", "[Без имени]"),
                )
                continue

            rule_counter[0] += 1
            rule_number = f"{parent_prefix}{rule_counter[0]}"
            formatted_rule = self.formatter.format(rule, rule_number, section_name, layer_path)

            resolved_rule = {
                "source": formatted_rule[6],
                "destination": formatted_rule[7],
                "service": formatted_rule[8],
                "action": formatted_rule[9],
                "track": formatted_rule[11],
                "enabled": formatted_rule[3],
                "comments": formatted_rule[13],
            }

            uid = rule.get("uid")
            current_layer_path = " / ".join(layer_path)

            print(f"  ▸ Проверка правила {rule_number}: {rule_name}")
            for check in self._get_check_methods():
                result = check(rule, resolved_rule)
                if result:
                    severity = result["severity"]
                    issue_text = f"   [{severity}] - [{result['issue']}]"
                    print(
                        f"    {issue_text} в правиле '{rule_name}' (номер: {rule_number}) слоя '{current_layer_path}'"
                    )
                    self.findings.append(
                        {
                            "layer": current_layer_path,
                            "rule_number": rule_number,
                            "rule_uid": uid,
                            "rule_name": rule_name,
                            "issue": result["issue"],
                            "severity": severity,
                            "rule": resolved_rule,
                        }
                    )

            if "inline-layer" in rule:
                nested_uid = rule["inline-layer"]
                nested_name = self.resolver.get_layer_name_by_uid(nested_uid)
                nested_rules = self.policies.get(nested_name)
                if nested_rules:
                    print(f"    🔁 Переход в inline-layer: {nested_name}")
                    self._process_rules(
                        nested_rules,
                        layer_path + [nested_name],
                        parent_prefix=f"{rule_number}.",
                        rule_counter=[0],
                    )

    def _get_check_methods(self):
        checks = []
        if self.enabled_checks.get("any_to_any_accept"):
            checks.append(self._check_any_to_any_accept)
        if self.enabled_checks.get("no_track"):
            checks.append(self._check_no_track)
        if self.enabled_checks.get("hit_count_zero"):
            checks.append(self._check_hit_count_zero)
        if self.enabled_checks.get("disabled_rule"):
            checks.append(self._check_disabled_rule)
        if self.enabled_checks.get("any_service_accept"):
            checks.append(self._check_any_service_accept)
        if self.enabled_checks.get("any_destination_accept"):
            checks.append(self._check_any_destination_accept)
        if self.enabled_checks.get("any_source_accept"):
            checks.append(self._check_any_source_accept)
        return checks

    # --- Проверки ---
    def _check_any_to_any_accept(self, rule, resolved):
        if (
            "Any (CpmiAnyObject)" in resolved["source"]
            and "Any" in resolved["destination"]
            and resolved["action"].startswith("Accept")
        ):
            return {"issue": "Any / Any → Accept", "severity": "Critical"}

    def _check_no_track(self, rule, resolved):
        if "None (Track)" in resolved["track"]:
            return {"issue": "No Track configured", "severity": "High"}

    def _check_hit_count_zero(self, rule, resolved):
        hit = rule.get("hits", {}).get("value")
        if hit == 0:
            return {"issue": "Hit count is zero", "severity": "Medium"}

    def _check_disabled_rule(self, rule, resolved):
        if resolved["enabled"] is False:
            return {"issue": "Rule is disabled", "severity": "Info"}

    def _check_any_service_accept(self, rule, resolved):
        if "Any (CpmiAnyObject)" in resolved["service"] and resolved["action"].startswith("Accept"):
            return {"issue": "Service is Any in Accept Rule", "severity": "Medium"}

    def _check_any_destination_accept(self, rule, resolved):
        if "Any (CpmiAnyObject)" in resolved["destination"] and resolved["action"].startswith(
            "Accept"
        ):
            return {"issue": "Destination is Any in Accept Rule", "severity": "High"}

    def _check_any_source_accept(self, rule, resolved):
        if "Any (CpmiAnyObject)" in resolved["source"] and resolved["action"].startswith("Accept"):
            return {"issue": "Source is Any in Accept Rule", "severity": "High"}

    def _build_summary(self):
        counter = Counter(f["severity"] for f in self.findings)
        if not counter:
            return "✅ Нарушений не найдено."
        lines = ["\n  📊 Сводка нарушений:"]
        for level in ["Critical", "High", "Medium", "Info"]:
            if level in counter:
                icon = self.SEVERITY_ICONS.get(level, "")
                lines.append(f"  {icon} {level}: {counter[level]}")
        return "\n".join(lines)
