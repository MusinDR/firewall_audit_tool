# services/fetch_service.py

from PyQt6.QtCore import QThread

from infrastructure.checkpoint_fetch_worker import FetchWorker


class FetchService:
    def __init__(self, client, policy_service, on_progress, on_result, on_error):
        self.client = client
        self.policy_service = policy_service
        self.on_progress = on_progress
        self.on_result = on_result
        self.on_error = on_error

        self.thread = QThread()
        self.worker = FetchWorker(client)
        self.worker.moveToThread(self.thread)

        # Подключаем сигналы
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.worker.progress.connect(self.on_progress)
        self.worker.error.connect(self.on_error)
        self.worker.result.connect(self.handle_result)

    def start(self):
        self.thread.start()

    def handle_result(self, policies, dict_objects, all_objects):
        try:
            self.policy_service.save_policies(policies, dict_objects, all_objects)
            self.on_result()
        except Exception as e:
            self.on_error(f"❌ Ошибка при сохранении: {e}")
