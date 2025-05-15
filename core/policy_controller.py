# core/policy_controller.py

from core.data_loader import load_all_data
from resolvers.object_resolver import ObjectResolver
from core.csv_exporter import CSVExporter

def export_selected_layer_to_csv(layer_name: str, output_path: str = "tmp/rules_export.csv"):
    policies, dict_objects, all_objects = load_all_data()
    resolver = ObjectResolver(all_objects, dict_objects)
    exporter = CSVExporter(policies, resolver)
    exporter.export_to_csv(output_path, selected_layer=layer_name)
