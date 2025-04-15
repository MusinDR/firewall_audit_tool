from checkpoint_client import CheckpointClient

client = CheckpointClient(
    server="192.168.3.10",
    username="admin",
    password="UserLoser228"
)
client.export_policies_to_json("policies.json")
client.export_objects_to_json("objects.json")