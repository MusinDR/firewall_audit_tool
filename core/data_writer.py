# core/data_writer.py

import json
import os

def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_all(policies: dict, dict_objects: dict, all_objects: list):
    save_json(policies, "tmp/policies.json")
    save_json(dict_objects, "tmp/objects-dictionary.json")
    save_json(all_objects, "tmp/all_objects.json")
