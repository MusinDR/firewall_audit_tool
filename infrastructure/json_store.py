# infrastructure/json_store.py

import json
import os


def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл не найден: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_all(policies: dict, dict_objects: dict, all_objects: list):
    save_json(policies, "tmp/policies.json")
    save_json(dict_objects, "tmp/objects-dictionary.json")
    save_json(all_objects, "tmp/all_objects.json")


def load_all_data() -> tuple[dict, dict, list]:
    policies = load_json("tmp/policies.json")
    dict_objects = load_json("tmp/objects-dictionary.json")
    all_objects = load_json("tmp/all_objects.json")
    return policies, dict_objects, all_objects
