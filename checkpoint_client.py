# checkpoint_client.py

from cpapi import APIClient, APIClientArgs
import json
import urllib3

#urllib3.disable_warnings()

class CheckpointClient:

    def __init__(self, server: str, username: str, password: str, print_func=print):
        self.server = server
        self.username = username
        self.password = password
        self.client = APIClient(APIClientArgs(server=server))
        self.print = print_func

    def login(self) -> bool:
        try:
            response = self.client.login(self.username, self.password)

            if not getattr(response, "success", False):
                print(f"❌ Ошибка авторизации: {getattr(response, 'error_message', 'Неизвестная ошибка')}")
                return False

            print("✅ Успешный вход")
            return True

        except Exception as e:
            print(f"❌ Исключение при попытке входа: {e}")
            return False

    def logout(self):
        self.client.api_call("logout")
        print("🔒 Сессия завершена")

    def get_all_policies(self) -> dict:
        policies_data = {}
        objects_data  = {}

        layers_resp = self.client.api_call("show-access-layers", {"details-level": "standard"})
        layers = layers_resp.data.get("access-layers", [])

        for layer in layers:
            layer_name = layer["name"]
            layer_uid = layer["uid"]
            print(f"📦 Слой: {layer_name}")

            offset = 0
            limit = 50
            total = 1
            rules_list = []
            objects_list = []

            while offset < total:
                rulebase_resp = self.client.api_call("show-access-rulebase", {
                    "name": layer_uid,
                    "offset": offset,
                    "limit": limit,
                    "show-hits": True,
                    "details-level": "full"
                })

                rules_rulebase = rulebase_resp.data.get("rulebase", [])
                objects_rulebase = rulebase_resp.data.get("objects-dictionary", [])

                total = rulebase_resp.data.get("total", 0)

                rules_list.extend(rules_rulebase)
                objects_list.extend(objects_rulebase)

                offset += limit

            policies_data[layer_name] = rules_list
            objects_data[layer_name] = objects_list

        return policies_data, objects_data

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
                print("❌ Ошибка при получении объектов:", resp.error_message)
                break

            page = resp.data.get("objects", [])
            total = resp.data.get("total", 0)

            print(f"  🔹 Загружено {len(page)} объектов (offset {offset})")
            all_objects.extend(page)
            offset += limit

        print(f"✅ Всего объектов: {len(all_objects)}")
        return all_objects

    def export_policies_to_json(self, rules_path: str, objects_path: str):
        if not self.login():
            return

        try:
            policies, objects = self.get_all_policies()

            with open(rules_path, "w", encoding="utf-8") as f:
                json.dump(policies, f, indent=2, ensure_ascii=False)
            print(f"✅ Экспорт завершён. Файл: {rules_path}")

            with open(objects_path, "w", encoding="utf-8") as f:
                json.dump(objects, f, indent=2, ensure_ascii=False)
            print(f"✅ Экспорт завершён. Файл: {objects_path}")

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
