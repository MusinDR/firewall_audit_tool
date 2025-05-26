# services/audit_service.py

from audit.audit_engine import RuleAuditor
from core.audit_controller import export_findings_to_csv
from core.data_io import load_all_data
from resolvers.object_resolver import ObjectResolver


class AuditService:
    def __init__(self, log_func=print):
        self.log = log_func

    def audit_layer(self, layer_name: str, checks: dict) -> tuple[list[dict], str]:
        policies, dict_objects, all_objects = load_all_data()
        resolver = ObjectResolver(all_objects, dict_objects)
        auditor = RuleAuditor(policies, resolver, enabled_checks=checks, log_func=self.log)
        findings, summary = auditor.run_audit(selected_layer=layer_name)
        return findings, summary

    def export_findings(self, findings: list[dict], path: str):
        export_findings_to_csv(findings, path)
