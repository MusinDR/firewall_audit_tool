from checkpoint_client import CheckpointClient
from object_resolver import ObjectResolver
import json


client = CheckpointClient(
    server="192.168.3.10",
    username="admin",
    password="UserLoser228"
)

client.export_policies_to_json("policies.json")
client.export_objects_to_json("objects.json")

with open("objects.json", "r", encoding="utf-8") as f:
    all_objects = json.load(f)

resolver = ObjectResolver(all_objects)

uid = "5738d1a9-c484-4f4f-ab8f-a215e215279c"
print(resolver.format(uid))
uid = "d0eb14b0-fa36-4955-a3db-1896fb2089d9"
print(resolver.format(uid))
uid = "4e4a450c-6a62-44a6-b974-aac64f8b1dd8"
print(resolver.format(uid))