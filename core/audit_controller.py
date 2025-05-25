import csv
from collections import defaultdict

from audit.audit_engine import RuleAuditor
from core.data_loader import load_all_data
from resolvers.object_resolver import ObjectResolver

SEVERITY_ORDER = {"Critical": 4, "High": 3, "Medium": 2, "Info": 1}

SEVERITY_ICONS = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Info": "🔵"}


def run_audit_and_export(
    layer_name: str, audit_checks: dict, output_path: str = "tmp/audit_findings.csv"
) -> tuple[int, str]:
    policies, dict_objects, all_objects = load_all_data()
    resolver = ObjectResolver(all_objects, dict_objects)
    auditor = RuleAuditor(policies, resolver, enabled_checks=audit_checks)
    findings, summary = auditor.run_audit(selected_layer=layer_name)

    if findings:
        export_findings_to_csv(findings, output_path)

    return len(findings), summary


def export_findings_to_csv(findings: list[dict], filepath: str):
    grouped = defaultdict(list)
    for finding in findings:
        grouped[finding["rule_uid"]].append(finding)

    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
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
                "Comments",
            ]
        )

        for uid, issues in grouped.items():
            rule_data = issues[0]["rule"]
            max_severity = max(
                (i["severity"] for i in issues), key=lambda s: SEVERITY_ORDER.get(s, 0)
            )
            display_severity = f"{SEVERITY_ICONS.get(max_severity)} {max_severity}"
            issues_joined = "; ".join(sorted(set(i["issue"] for i in issues)))

            writer.writerow(
                [
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
                    rule_data.get("comments", ""),
                ]
            )
