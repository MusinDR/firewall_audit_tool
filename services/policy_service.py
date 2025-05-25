# services/policy_service.py

from core.data_loader import load_json
from core.data_writer import save_all
from core.policy_controller import export_selected_layer_to_csv


class PolicyService:
    def save_policies(self, policies, dict_objects, all_objects):
        save_all(policies, dict_objects, all_objects)

    def get_policy_layers(self) -> list[str]:
        data = load_json("tmp/policies.json")
        return list(data.keys())

    def export_layer(self, layer: str, path: str = "tmp/rules_export.csv"):
        export_selected_layer_to_csv(layer, output_path=path)
