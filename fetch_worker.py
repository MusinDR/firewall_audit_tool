from PyQt6.QtCore import QObject, QThread, pyqtSignal


class FetchWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    result = pyqtSignal(dict, dict, list)  # policies, dict_objects, all_objects

    def __init__(self, client: 'CheckpointClient'):
        super().__init__()
        self.client = client

    def run(self):
        try:
            self.progress.emit("🚀 Начинаем подключение к CheckPoint...")
            if not self.client.login():
                self.error.emit("❌ Ошибка авторизации")
                self.finished.emit()
                return

            self.progress.emit("📡 Получаем политики...")
            policies, dict_objects = self.client.get_all_policies()

            self.progress.emit("📡 Получаем объекты...")
            all_objects = self.client.get_all_objects()

            self.progress.emit("✅ Данные успешно получены")
            self.result.emit(policies, dict_objects, all_objects)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.client.logout()
            self.finished.emit()
