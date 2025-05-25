# core/data_loader.py

import json
import os


def load_json(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл не найден: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_all_data():
    policies = load_json("tmp/policies.json")
    dict_objects = load_json("tmp/objects-dictionary.json")
    all_objects = load_json("tmp/all_objects.json")
    return policies, dict_objects, all_objects
