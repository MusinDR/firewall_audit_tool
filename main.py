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

uid = "d2a9c4cd-e40e-4b40-ad0f-5f35d364b494"
obj = resolver.get(uid)

if obj:
    print("Имя объекта:", obj.get("name"))
    print("Тип объекта:", obj.get("type"))
    print("Полный объект:", obj)
else:
    print("❌ Объект не найден")

