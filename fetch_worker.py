from PyQt6.QtCore import QObject, QThread, pyqtSignal
import json


class FetchWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    result = pyqtSignal(dict, dict, list)

    def __init__(self, client: 'CheckpointClient'):
        super().__init__()
        self.client = client

    def run(self):
        try:
            self.progress.emit("▶ Начинаем подключение к CheckPoint...")
            if not self.client.login():
                self.error.emit("❌ Ошибка авторизации")
                self.finished.emit()
                return

            self.progress.emit("📡 Получаем политики...")
            policies, dict_objects = self.client.get_all_policies()
            self.progress.emit("📡 Получаем объекты...")
            all_objects = self.client.get_all_objects()

            with open("policies.json", "w", encoding="utf-8") as f:
                json.dump(policies, f, indent=2, ensure_ascii=False)
            with open("objects-dictionary.json", "w", encoding="utf-8") as f:
                json.dump(dict_objects, f, indent=2, ensure_ascii=False)
            with open("all_objects.json", "w", encoding="utf-8") as f:
                json.dump(all_objects, f, indent=2, ensure_ascii=False)

            self.result.emit(policies, dict_objects, all_objects)
            self.progress.emit("✅ Данные успешно выгружены")
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.client.logout()
            self.finished.emit()
