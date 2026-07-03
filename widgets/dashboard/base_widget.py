# widgets/dashboard/base_widget.py
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QVBoxLayout, QLabel


class BaseDashboardWidget(QWidget):
    """
    Базовый класс для всех виджетов дашборда.

    Данные:
        self._df       — pandas DataFrame текущего датасета (None до загрузки)
        self._datasets — dict[name → df]  (все загруженные датасеты)

    Поток данных:
        ConfiguratorWindow → set_datasets(datasets) → _apply_settings()
    Настройки виджета хранят 'dataset_name' (str) — ключ в self._datasets.
    """

    edit_requested = Signal()

    def __init__(self, settings: dict = None, parent=None):
        super().__init__(parent)
        self._settings: dict = {}
        self._datasets: dict = {}   # name → DataFrame
        self._df       = None       # текущий df (по dataset_name)

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # Заголовок
        self._header = QWidget()
        self._header.setStyleSheet("background: transparent;")
        self._header_layout = QHBoxLayout(self._header)
        self._header_layout.setContentsMargins(6, 2, 6, 2)
        self._header_layout.setSpacing(0)

        self._title_label = QLabel()
        self._title_label.setStyleSheet(
            "font-weight: 600; font-size: 11px; color: #64748B; background: transparent;"
        )
        self._header_layout.addWidget(self._title_label)
        self._header_layout.addStretch()

        self._edit_btn = QPushButton("⋮")
        self._edit_btn.setFixedSize(24, 24)
        self._edit_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                font-size: 16px; font-weight: bold; color: #475569;
            }
            QPushButton:hover {
                color: #38BDF8; background: #2D3E56; border-radius: 4px;
            }
        """)
        self._edit_btn.clicked.connect(self._on_edit_clicked)
        self._header_layout.addWidget(self._edit_btn)

        # Контейнер содержимого
        self._content_container = QWidget()
        self._content_container.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(self._content_container)
        self._content_layout.setContentsMargins(4, 4, 4, 4)
        self._content_layout.setSpacing(4)

        self._main_layout.addWidget(self._header)
        self._main_layout.addWidget(self._content_container, 1)

        if settings:
            self.set_settings(settings)

    # ─── Public API ───────────────────────────────────────────────────────────

    def set_settings(self, settings: dict) -> None:
        self._settings = settings.copy()
        self._update_title()
        self._refresh_df()
        self._apply_settings()

    def settings(self) -> dict:
        return self._settings.copy()

    def set_data(self, df) -> None:
        """Устаревший метод: устанавливает один DataFrame напрямую."""
        self._df = df
        self._apply_settings()

    def set_datasets(self, datasets: dict) -> None:
        """Передаёт все датасеты; выбирает нужный по dataset_name из настроек."""
        self._datasets = datasets
        self._refresh_df()
        self._apply_settings()

    def serialize(self) -> dict:
        return self._settings.copy()

    def deserialize(self, data: dict) -> None:
        self.set_settings(data)

    def refresh(self) -> None:
        self._apply_settings()

    # ─── Internal ─────────────────────────────────────────────────────────────

    def _refresh_df(self):
        """Обновляет self._df из self._datasets по ключу dataset_name."""
        name = self._settings.get('dataset_name', '')
        if name and self._datasets:
            self._df = self._datasets.get(name)
        # Если нет dataset_name — df может быть уже установлен через set_data, не сбрасываем

    def _apply_settings(self):
        """Переопределяется в наследниках."""
        pass

    def _update_title(self):
        title = self._settings.get('title', '')
        self._title_label.setText(title)

    def _on_edit_clicked(self):
        self.edit_requested.emit()
