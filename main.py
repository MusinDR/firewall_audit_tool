from checkpoint_client import CheckpointClient
from object_resolver import ObjectResolver
from csv_exporter import CSVExporter
import json


client = CheckpointClient(
    server="192.168.3.10",
    username="admin",
    password="UserLoser228"
)

client.export_policies_to_json("policies.json", "objects-dictionary.json")
#client.export_objects_to_json("all_objects.json")

with open("all_objects.json", "r", encoding="utf-8") as f:
    all_objects = json.load(f)

with open("objects-dictionary.json", "r", encoding="utf-8") as f:
    objects_dictionary = json.load(f)

with open("policies.json", "r", encoding="utf-8") as f:
    policies = json.load(f)

resolver = ObjectResolver(all_objects, objects_dictionary)

#uid = "5738d1a9-c484-4f4f-ab8f-a215e215279c"
#print(resolver.format(uid))
#uid = "d0eb14b0-fa36-4955-a3db-1896fb2089d9"
#print(resolver.format(uid))
#uid = "4e4a450c-6a62-44a6-b974-aac64f8b1dd8"
#print(resolver.format(uid))
#uid = "6c488338-8eec-4103-ad21-cd461ac2c472"
#print(resolver.format(uid))
#uid = "598ead32-aa42-4615-90ed-f51a5928d41d"
#print(resolver.format(uid))

exporter = CSVExporter(policies, resolver)
exporter.export_to_csv("rules_export.csv", "New_Access Layer")