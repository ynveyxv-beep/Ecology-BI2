# core/ai_worker.py
"""
QThread-воркеры для фоновой загрузки модели и инференса.
Позволяют не блокировать интерфейс во время тяжёлых операций.
"""

from PySide6.QtCore import QThread, Signal


class AILoadWorker(QThread):
    """Загружает GGUF-модель в фоновом потоке."""

    finished = Signal(bool, str)   # (успех, сообщение_об_ошибке)

    def __init__(self, client, parent=None):
        super().__init__(parent)
        self._client = client

    def run(self):
        ok = self._client.load_model()
        self.finished.emit(ok, self._client.load_error or "")


class AIInferenceWorker(QThread):
    """Выполняет один запрос к модели в фоновом потоке."""

    response_ready = Signal(dict)   # результат из AIClient.ask()
    error_occurred = Signal(str)

    def __init__(self, client, message: str, datasets: dict, parent=None):
        super().__init__(parent)
        self._client   = client
        self._message  = message
        self._datasets = datasets

    def run(self):
        try:
            result = self._client.ask(self._message, self._datasets)
            self.response_ready.emit(result)
        except Exception as exc:
            self.error_occurred.emit(str(exc))
