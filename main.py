from checkpoint_client import CheckpointClient
from object_resolver import ObjectResolver
import json


client = CheckpointClient(
    server="192.168.3.10",
    username="admin",
    password="UserLoser228"
)

#client.export_policies_to_json("policies.json")
#client.export_objects_to_json("objects.json")

with open("objects.json", "r", encoding="utf-8") as f:
    all_objects = json.load(f)

resolver = ObjectResolver(all_objects)

uid = "96b71c65-16eb-4426-a6c9-20f5b711ef09"
print(resolver.format(uid))