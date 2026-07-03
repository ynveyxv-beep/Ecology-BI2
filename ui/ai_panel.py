# ui/ai_panel.py
"""
Сворачиваемая боковая панель AI-ассистента.
Встраивается в ConfiguratorWindow справа.

Публичные сигналы:
  action_requested(dict)  — AI хочет создать виджет, передаёт action-словарь
"""

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QScrollArea, QLineEdit, QFrame, QScrollBar
)

from core.ai_client import get_client
from core.ai_worker import AILoadWorker, AIInferenceWorker
import ui.theme as _tm
from ui.theme import (
    BG_DEEP, BG_PANEL, BG_CARD, BG_HOVER, BG_ACTIVE,
    BORDER, BORDER_LT, BORDER_ACC,
    TEXT_PRI, TEXT_SEC, TEXT_MUT,
    ACCENT, ACCENT_DARK,
)

_PANEL_WIDTH = 288


# ─── Пузырёк сообщения ────────────────────────────────────────────────────────

class _Bubble(QFrame):
    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(parent)
        bg    = BG_ACTIVE if is_user else BG_CARD
        color = TEXT_PRI  if is_user else TEXT_SEC
        self.setStyleSheet(
            f"QFrame{{background:{bg};border:1px solid {BORDER};"
            f"border-radius:8px;margin:1px 2px;}}"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 7, 10, 7)
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f"color:{color};font-size:12px;background:transparent;border:none;"
        )
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(lbl)


# ─── Основная панель ──────────────────────────────────────────────────────────

class AIPanelWidget(QWidget):
    """
    Панель AI-ассистента шириной 288 пикселей.
    Показывается / скрывается через toggle().
    """

    action_requested = Signal(dict)   # {"action":"create_widget","type":...,"config":{...}}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._datasets: dict = {}
        self._infer_worker = None
        self._load_worker  = None
        self._client = get_client()

        self.setFixedWidth(_PANEL_WIDTH)
        self.setStyleSheet(
            f"AIPanelWidget{{background:{BG_PANEL};border-left:1px solid {BORDER};}}"
        )
        self.hide()

        self._build_ui()
        self._begin_load()

    # ── Построение UI ─────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_header())
        root.addWidget(self._make_status())
        root.addWidget(self._make_chat_area(), 1)
        root.addWidget(self._make_input_bar())

        # Первое приветствие
        self._add_bubble(
            "Привет! Я помогу вам создавать виджеты и анализировать данные.\n\n"
            "Попробуйте написать:\n«добавь столбчатый график расхода воды по месяцам»\n"
            "или задайте вопрос по загруженным данным.",
            is_user=False,
        )

    def _make_header(self) -> QWidget:
        w = QWidget()
        self._header_w = w
        w.setFixedHeight(44)
        w.setStyleSheet(f"background:{BG_DEEP};border-bottom:1px solid {BORDER};")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(12, 0, 8, 0)

        icon = QLabel("🤖")
        icon.setStyleSheet("font-size:15px;background:transparent;border:none;")
        lay.addWidget(icon)

        title = QLabel("AI-ассистент")
        title.setStyleSheet(
            f"color:{TEXT_PRI};font-size:13px;font-weight:bold;"
            f"background:transparent;border:none;"
        )
        lay.addWidget(title, 1)

        btn = QPushButton("✕")
        btn.setFixedSize(28, 28)
        btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;color:{TEXT_MUT};font-size:14px;}}"
            f"QPushButton:hover{{color:{TEXT_PRI};}}"
        )
        btn.clicked.connect(self.hide)
        lay.addWidget(btn)
        return w

    def _make_status(self) -> QLabel:
        lbl = QLabel("⏳ Загрузка модели…")
        lbl.setFixedHeight(26)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            f"color:{TEXT_MUT};font-size:11px;background:{BG_DEEP};"
            f"border-bottom:1px solid {BORDER};padding:0 8px;"
        )
        self._status_lbl = lbl
        return lbl

    def _make_chat_area(self) -> QScrollArea:
        self._chat_box = QWidget()
        self._chat_box.setStyleSheet(f"background:{BG_DEEP};")
        self._chat_lay = QVBoxLayout(self._chat_box)
        self._chat_lay.setContentsMargins(8, 8, 8, 8)
        self._chat_lay.setSpacing(6)
        self._chat_lay.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(self._chat_box)
        scroll.setStyleSheet(
            f"QScrollArea{{background:{BG_DEEP};border:none;}}"
            f"QScrollBar:vertical{{background:{BG_PANEL};width:5px;border:none;}}"
            f"QScrollBar::handle:vertical{{background:{BORDER};border-radius:2px;}}"
        )
        self._scroll = scroll
        return scroll

    def _make_input_bar(self) -> QWidget:
        bar = QWidget()
        self._input_bar_w = bar
        bar.setFixedHeight(56)
        bar.setStyleSheet(f"background:{BG_PANEL};border-top:1px solid {BORDER};")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Введите запрос…")
        self._input.setStyleSheet(
            f"QLineEdit{{background:{BG_CARD};border:1px solid {BORDER};"
            f"border-radius:6px;padding:6px 10px;font-size:12px;color:{TEXT_PRI};}}"
            f"QLineEdit:focus{{border-color:{ACCENT};}}"
            f"QLineEdit:disabled{{color:{TEXT_MUT};}}"
        )
        self._input.returnPressed.connect(self._send)
        lay.addWidget(self._input, 1)

        self._send_btn = QPushButton("→")
        self._send_btn.setFixedSize(36, 36)
        self._send_btn.setEnabled(False)
        self._send_btn.setStyleSheet(
            f"QPushButton{{background:{ACCENT_DARK};border:none;border-radius:6px;"
            f"color:{TEXT_PRI};font-size:17px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{ACCENT};color:#0F1A0F;}}"
            f"QPushButton:disabled{{background:{BORDER};color:{TEXT_MUT};}}"
        )
        self._send_btn.clicked.connect(self._send)
        lay.addWidget(self._send_btn)
        return bar

    # ── Загрузка модели ───────────────────────────────────────────────────────

    def _begin_load(self):
        if self._client.is_loaded:
            self._on_loaded(True, "")
            return
        self._load_worker = AILoadWorker(self._client)
        self._load_worker.finished.connect(self._on_loaded)
        self._load_worker.start()

    def _on_loaded(self, ok: bool, err: str):
        if ok:
            self._status_lbl.setText("✅ Готово · Qwen2.5-0.5B")
            self._status_lbl.setStyleSheet(
                f"color:#4CAF50;font-size:11px;background:{BG_DEEP};"
                f"border-bottom:1px solid {BORDER};padding:0 8px;"
            )
            self._send_btn.setEnabled(True)
            self._input.setEnabled(True)
        else:
            msg = err or "Модель не найдена"
            self._status_lbl.setText(f"❌ {msg}")
            self._status_lbl.setStyleSheet(
                f"color:#F44336;font-size:11px;background:{BG_DEEP};"
                f"border-bottom:1px solid {BORDER};padding:0 8px;"
            )
            self._add_bubble(
                f"⚠️ Не удалось загрузить AI:\n{msg}\n\n"
                "Убедитесь, что файл models/qwen2.5-0.5b-instruct-q4_k_m.gguf "
                "находится рядом с программой.",
                is_user=False,
            )

    # ── Отправка сообщения ────────────────────────────────────────────────────

    def _send(self):
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self._add_bubble(text, is_user=True)
        self._set_busy(True)

        self._infer_worker = AIInferenceWorker(
            self._client, text, self._datasets
        )
        self._infer_worker.response_ready.connect(self._on_response)
        self._infer_worker.error_occurred.connect(self._on_infer_error)
        self._infer_worker.start()

    def _set_busy(self, busy: bool):
        self._send_btn.setEnabled(not busy)
        self._input.setEnabled(not busy)
        self._send_btn.setText("⋯" if busy else "→")

    def _on_response(self, result: dict):
        self._set_busy(False)
        rtype = result.get("type")

        if rtype == "widget":
            action = result["action"]
            cfg    = action.get("config", {})
            title  = cfg.get("title", "виджет")
            wtype  = action.get("type", "chart")
            self._add_bubble(
                f"✅ Создаю «{title}» ({wtype})\nВиджет появится на дашборде.",
                is_user=False,
            )
            self.action_requested.emit(action)

        elif rtype == "error":
            self._add_bubble(f"⚠️ {result.get('text','Ошибка')}", is_user=False)

        else:
            self._add_bubble(result.get("text", ""), is_user=False)

    def _on_infer_error(self, err: str):
        self._set_busy(False)
        self._add_bubble(f"⚠️ Ошибка: {err}", is_user=False)

    # ── Вспомогательные методы ────────────────────────────────────────────────

    def _add_bubble(self, text: str, *, is_user: bool):
        """Добавляет пузырёк в чат и прокручивает вниз."""
        # Убираем старый stretch
        cnt = self._chat_lay.count()
        if cnt:
            self._chat_lay.takeAt(cnt - 1)

        self._chat_lay.addWidget(_Bubble(text, is_user))
        self._chat_lay.addStretch()

        # Прокрутка вниз с небольшой задержкой (пока виджет не отрисован)
        QTimer.singleShot(60, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def toggle(self):
        """Показать / скрыть панель."""
        if self.isVisible():
            self.hide()
        else:
            self.show()

    # ── Публичный API ─────────────────────────────────────────────────────────

    def set_datasets(self, datasets: dict):
        """Обновить контекст датасетов (вызывается при изменении датасетов)."""
        self._datasets = datasets

    def refresh_theme(self) -> None:
        """Переприменяет цвета из текущей темы ко всем виджетам панели."""
        tm = _tm
        self.setStyleSheet(
            f"AIPanelWidget{{background:{tm.BG_PANEL};border-left:1px solid {tm.BORDER};}}"
        )
        # Header
        if hasattr(self, '_header_w'):
            self._header_w.setStyleSheet(
                f"background:{tm.BG_DEEP};border-bottom:1px solid {tm.BORDER};"
            )
        # Status label
        if hasattr(self, '_status_lbl'):
            cur = self._status_lbl.text()
            ok  = cur.startswith("✅")
            color = "#4CAF50" if ok else tm.TEXT_MUT
            self._status_lbl.setStyleSheet(
                f"color:{color};font-size:11px;background:{tm.BG_DEEP};"
                f"border-bottom:1px solid {tm.BORDER};padding:0 8px;"
            )
        # Chat scroll area background
        if hasattr(self, '_chat_box'):
            self._chat_box.setStyleSheet(f"background:{tm.BG_DEEP};")
        if hasattr(self, '_scroll'):
            self._scroll.setStyleSheet(
                f"QScrollArea{{background:{tm.BG_DEEP};border:none;}}"
                f"QScrollBar:vertical{{background:{tm.BG_PANEL};width:5px;border:none;}}"
                f"QScrollBar::handle:vertical{{background:{tm.BORDER};border-radius:2px;}}"
            )
        # Input bar
        if hasattr(self, '_input_bar_w'):
            self._input_bar_w.setStyleSheet(
                f"background:{tm.BG_PANEL};border-top:1px solid {tm.BORDER};"
            )
        if hasattr(self, '_input'):
            self._input.setStyleSheet(
                f"QLineEdit{{background:{tm.BG_CARD};border:1px solid {tm.BORDER};"
                f"border-radius:6px;padding:6px 10px;font-size:12px;color:{tm.TEXT_PRI};}}"
                f"QLineEdit:focus{{border-color:{tm.ACCENT};}}"
                f"QLineEdit:disabled{{color:{tm.TEXT_MUT};}}"
            )
        if hasattr(self, '_send_btn'):
            self._send_btn.setStyleSheet(
                f"QPushButton{{background:{tm.ACCENT_DARK};border:none;border-radius:6px;"
                f"color:{tm.TEXT_PRI};font-size:17px;font-weight:bold;}}"
                f"QPushButton:hover{{background:{tm.ACCENT};color:#0F1A0F;}}"
                f"QPushButton:disabled{{background:{tm.BORDER};color:{tm.TEXT_MUT};}}"
            )
