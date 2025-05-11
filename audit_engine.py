class RuleAuditor:
    DEFAULT_CHECKS = {
        "any_to_any_accept": True,
        "no_track": True,
        "hit_count_zero": True,
        "disabled_rule": True,
        "any_service_accept": True,
        "any_destination_accept": True,
        "any_source_accept": True
    }

    def __init__(self, policies: dict, resolver, enabled_checks: dict = None):
        self.policies = policies
        self.resolver = resolver
        self.enabled_checks = enabled_checks or self.DEFAULT_CHECKS
        self.findings = []

    def run_audit(self, selected_layer: str = None) -> list[dict]:
        print("▶ Запуск аудита...")
        layers = [selected_layer] if selected_layer else list(self.policies.keys())
        for layer in layers:
            print(f"🔍 Слой: {layer}")
            rules = self.policies.get(layer)
            if not rules:
                continue
            print(f"🔍 Слой: {layer} ({len(rules)} правил)")
            self._process_rules(rules, layer)
        print(f"Нарушений найдено: {len(self.findings)}")
        print(f"Нарушений найдено: {len(self.findings)}")
        return self.findings

    def _process_rules(self, rules, layer, parent_prefix=""):
        for index, rule in enumerate(rules, start=1):
            rule_name = rule.get("name", "")
            rule_number = f"{parent_prefix}{index}"
            resolved_rule = self._resolve_rule(rule)
            uid = rule.get("uid")
            name = rule.get("name", "")

            print(f"  ▸ Проверка правила {rule_number}: {name}")
            any_issue = False
            for check in self._get_check_methods():
                result = check(rule, resolved_rule)
                if result:
                    any_issue = True
                    print(f"    🚨 Нарушение: {result['issue']} ({result['severity']}) в правиле '{rule.get('name', '')}' слоя '{layer}', номер: {rule_number}")
                    self.findings.append({
                        "layer": layer,
                        "rule_number": rule_number,
                        "rule_uid": uid,
                        "rule_name": name,
                        "issue": result["issue"],
                        "severity": result["severity"],
                        "rule": resolved_rule
                    })
            if not any_issue:
                print("     ✔ Нет нарушений")

            if "inline-layer" in rule:
                nested_uid = rule["inline-layer"]
                nested_layer = self.resolver.get_layer_name_by_uid(nested_uid)
                nested_rules = self.policies.get(nested_layer)
                if nested_rules:
                    print(f"  🔁 Переход в inline-layer: {nested_layer} ({len(nested_rules)} правил)")
                    self._process_rules(nested_rules, layer, parent_prefix=f"{rule_number}.")

    def _resolve_rule(self, rule) -> dict:
        return {
            "source": self._format_list(rule.get("source")),
            "destination": self._format_list(rule.get("destination")),
            "service": self._format_list(rule.get("service")),
            "action": self._format_item(rule.get("action")),
            "track": self._format_item((rule.get("track") or {}).get("type")),
            "enabled": rule.get("enabled"),
            "comments": rule.get("comments", "")
        }

    def _format_list(self, items):
        if not items:
            return ""
        return "; ".join([
            self.resolver.format(obj.get("uid") if isinstance(obj, dict) else obj)
            for obj in items
        ])

    def _format_item(self, item):
        if isinstance(item, dict):
            return self.resolver.format(item.get("uid"))
        if isinstance(item, str):
            return self.resolver.format(item)
        return ""

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

    def _check_any_to_any_accept(self, rule, resolved):
        if resolved["source"].startswith("Any") and resolved["destination"].startswith("Any") and resolved["action"].startswith("Accept"):
            return {"issue": "Any → Any → Accept", "severity": "critical"}

    def _check_no_track(self, rule, resolved):
        if not resolved["track"]:
            return {"issue": "No Track configured", "severity": "high"}

    def _check_hit_count_zero(self, rule, resolved):
        hit = rule.get("hits", {}).get("value")
        if hit == 0:
            return {"issue": "Hit count is zero", "severity": "medium"}

    def _check_disabled_rule(self, rule, resolved):
        if resolved["enabled"] is False:
            return {"issue": "Rule is disabled", "severity": "info"}

    def _check_any_service_accept(self, rule, resolved):
        if resolved["service"].startswith("Any") and resolved["action"].startswith("Accept"):
            return {"issue": "Service is Any with Accept", "severity": "medium"}

    def _check_any_destination_accept(self, rule, resolved):
        if resolved["destination"].startswith("Any") and resolved["action"].startswith("Accept"):
            return {"issue": "Destination is Any with Accept", "severity": "medium"}

    def _check_any_source_accept(self, rule, resolved):
        if resolved["source"].startswith("Any") and resolved["action"].startswith("Accept"):
            return {"issue": "Source is Any with Accept", "severity": "medium"}
