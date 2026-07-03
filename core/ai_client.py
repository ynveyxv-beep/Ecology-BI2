# core/ai_client.py
"""
Лёгкий локальный AI-клиент на базе llama-cpp-python.
Модель: qwen2.5-0.5b-instruct-q4_k_m.gguf (~370 МБ, ~500 МБ RAM).
Работает полностью офлайн, без внешних сервисов.
"""

import os
import sys
import json
import re
from typing import Optional

try:
    from llama_cpp import Llama
    _LLAMA_AVAILABLE = True
except ImportError:
    _LLAMA_AVAILABLE = False

# ─── Поиск модели ─────────────────────────────────────────────────────────────

_MODEL_FILENAME = "qwen2.5-0.5b-instruct-q4_k_m.gguf"


def _find_model() -> Optional[str]:
    """Ищет GGUF-файл рядом с exe или в папке проекта."""
    candidates = []

    # Собранное PyInstaller приложение
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
        candidates += [
            os.path.join(base, 'models', _MODEL_FILENAME),
            os.path.join(base, _MODEL_FILENAME),
        ]

    # Режим разработки
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    candidates += [
        os.path.join(root, 'models', _MODEL_FILENAME),
        os.path.join(os.getcwd(), 'models', _MODEL_FILENAME),
    ]

    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


# ─── Системный промпт ─────────────────────────────────────────────────────────

_SYSTEM = """\
Ты — AI-ассистент экологического дашборда EcoLens.
Отвечаешь только на русском языке, кратко и по делу.

Доступные типы виджетов:
- kpi     — одно число / ключевой показатель
- chart   — диаграмма (chart_type: bar | line | pie | scatter)
- table   — таблица данных
- text    — текстовый блок / заголовок

ПРАВИЛА:
1. Если пользователь просит СОЗДАТЬ виджет, график, диаграмму или показатель —
   ответь СТРОГО JSON и НИЧЕГО БОЛЬШЕ:
   {"action":"create_widget","type":"ТИП","config":{"title":"...","dataset":"...","x_column":"...","y_column":"...","chart_type":"bar"}}

2. Если пользователь задаёт ВОПРОС по данным — отвечай обычным текстом.

3. Если нет загруженных данных — сообщи об этом.

Загруженные датасеты:
{datasets}
"""


# ─── AI-клиент ────────────────────────────────────────────────────────────────

class AIClient:
    """Обёртка над llama-cpp-python. Один экземпляр на всё приложение."""

    def __init__(self):
        self._llm: Optional[object] = None
        self._loaded = False
        self._error: Optional[str] = None

    # ── свойства ──────────────────────────────────────────────────────────────

    @property
    def is_available(self) -> bool:
        return _LLAMA_AVAILABLE

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def load_error(self) -> Optional[str]:
        return self._error

    # ── загрузка ──────────────────────────────────────────────────────────────

    def load_model(self) -> bool:
        """
        Загружает модель. Вызывать из фонового потока, чтобы не блокировать UI.
        Возвращает True при успехе.
        """
        if not _LLAMA_AVAILABLE:
            self._error = "llama-cpp-python не установлен"
            return False

        model_path = _find_model()
        if not model_path:
            self._error = (
                f"Файл модели не найден: models/{_MODEL_FILENAME}\n"
                "Запустите build.bat — он скачает модель автоматически."
            )
            return False

        try:
            self._llm = Llama(
                model_path=model_path,
                n_ctx=2048,      # контекст — достаточно для наших задач
                n_threads=4,     # число потоков CPU
                n_batch=256,
                n_gpu_layers=0,  # только CPU — нет зависимости от GPU
                verbose=False,
            )
            self._loaded = True
            self._error = None
            return True
        except Exception as exc:
            self._error = str(exc)
            return False

    # ── инференс ──────────────────────────────────────────────────────────────

    def ask(self, message: str, datasets: dict) -> dict:
        """
        Отправляет сообщение модели.
        Возвращает:
          {"type": "widget", "action": {...}}  — создать виджет
          {"type": "text",   "text":   "..."}  — текстовый ответ
          {"type": "error",  "text":   "..."}  — ошибка
        """
        if not self._loaded:
            return {"type": "error", "text": "Модель не загружена"}

        # Формируем контекст датасетов
        if datasets:
            lines = []
            for name, df in datasets.items():
                cols = ", ".join(
                    f"{c} ({str(df[c].dtype)})" for c in list(df.columns)[:12]
                )
                lines.append(f"• {name}: [{cols}]")
            ds_ctx = "\n".join(lines)
        else:
            ds_ctx = "Нет загруженных датасетов"

        system = _SYSTEM.format(datasets=ds_ctx)

        try:
            resp = self._llm.create_chat_completion(
                messages=[
                    {"role": "system",    "content": system},
                    {"role": "user",      "content": message},
                ],
                temperature=0.05,   # детерминированный — нужен чёткий JSON
                max_tokens=400,
            )
            raw: str = resp["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            return {"type": "error", "text": f"Ошибка: {exc}"}

        # Пытаемся найти JSON в ответе
        json_m = re.search(r'\{[\s\S]*?\}', raw)
        if json_m:
            try:
                parsed = json.loads(json_m.group())
                if parsed.get("action") == "create_widget":
                    return {"type": "widget", "action": parsed}
            except json.JSONDecodeError:
                pass

        return {"type": "text", "text": raw}

    # ── выгрузка ──────────────────────────────────────────────────────────────

    def unload(self):
        """Освобождает RAM."""
        if self._llm is not None:
            del self._llm
            self._llm = None
        self._loaded = False


# ─── Глобальный синглтон ──────────────────────────────────────────────────────

_client = AIClient()


def get_client() -> AIClient:
    return _client
