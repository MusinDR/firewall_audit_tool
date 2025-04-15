# checkpoint_client.py

from cpapi import APIClient, APIClientArgs
import json
import urllib3

#urllib3.disable_warnings()

class CheckpointClient:

    def __init__(self, server: str, username: str, password: str):
        self.server = server
        self.username = username
        self.password = password
        self.client = APIClient(APIClientArgs(server=server))

    def login(self) -> bool:
        if not self.client.login(self.username, self.password):
            print("❌ Ошибка авторизации:", self.client.last_error_message())
            return False
        print("✅ Успешный вход")
        return True

    def logout(self):
        self.client.api_call("logout")
        print("🔒 Сессия завершена")

    def get_all_policies(self) -> dict:
        policies_data = {}

        layers_resp = self.client.api_call("show-access-layers", {"details-level": "standard"})
        layers = layers_resp.data.get("access-layers", [])

        for layer in layers:
            layer_name = layer["name"]
            layer_uid = layer["uid"]
            print(f"📦 Слой: {layer_name}")

            offset = 0
            limit = 50
            total = 1
            all_rules = []

            while offset < total:
                rulebase_resp = self.client.api_call("show-access-rulebase", {
                    "name": layer_uid,  # ← важно!
                    "offset": offset,
                    "limit": limit,
                    "details-level": "full"
                })

                rulebase = rulebase_resp.data.get("rulebase", [])
                total = rulebase_resp.data.get("total", 0)
                all_rules.extend(rulebase)

                offset += limit

            policies_data[layer_name] = all_rules

        return policies_data

    def get_all_objects(self) -> list:
        print("📦 Получаем список всех объектов...")
        all_objects = []

        offset = 0
        limit = 500
        total = 1

        while offset < total:
            resp = self.client.api_call("show-objects", {
                "offset": offset,
                "limit": limit,
                "details-level": "full"
            })

            if not resp.success:
                print("❌ Ошибка при получении объектов:", resp.error_message())
                break

            page = resp.data.get("objects", [])
            total = resp.data.get("total", 0)

            print(f"  🔹 Загружено {len(page)} объектов (offset {offset})")
            all_objects.extend(page)
            offset += limit

        print(f"✅ Всего объектов: {len(all_objects)}")
        return all_objects

    def export_policies_to_json(self, filepath: str):
        if not self.login():
            return

        try:
            policies = self.get_all_policies()

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(policies, f, indent=2, ensure_ascii=False)

            print(f"✅ Экспорт завершён. Файл: {filepath}")
        finally:
            self.logout()

    def export_objects_to_json(self, filepath: str):
        if not self.login():
            return

        try:
            objects = self.get_all_objects()

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(objects, f, indent=2, ensure_ascii=False)

            print(f"✅ Экспорт объектов завершен. Файл: {filepath}")
        finally:
            self.logout()
