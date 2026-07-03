# widgets/dashboard/image_widget.py
import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtGui import QPixmap

from widgets.dashboard.base_widget import BaseDashboardWidget


class ImageWidget(BaseDashboardWidget):
    """Виджет для отображения изображения."""

    def __init__(self, settings: dict = None, parent=None):
        # ВАЖНО: инициализируем _label до super().__init__(),
        # потому что BaseDashboardWidget.__init__ вызывает _apply_settings().
        self._label = None
        super().__init__(settings, parent)

        if self._label is None:
            self._label = QLabel()
            self._label.setAlignment(Qt.AlignCenter)
            self._label.setWordWrap(True)
            self._label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self._content_layout.addWidget(self._label)

        self._apply_settings()

    def _apply_settings(self):
        """Применяет настройки."""
        if self._label is None:
            return

        path    = self._settings.get('path', '')
        opacity = self._settings.get('opacity', 100)
        fit     = self._settings.get('fit', 'contain')

        if path and os.path.isfile(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                # Масштабирование по режиму fit
                lw = max(self._label.width(),  60)
                lh = max(self._label.height(), 40)
                if fit == 'cover':
                    scaled = pixmap.scaled(lw, lh, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                elif fit == 'fill':
                    scaled = pixmap.scaled(lw, lh, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                else:  # contain / center
                    scaled = pixmap.scaled(lw, lh, Qt.KeepAspectRatio, Qt.SmoothTransformation)

                # Прозрачность через stylesheet opacity
                op = opacity / 100.0
                self._label.setStyleSheet(f"opacity: {op:.2f};")
                self._label.setPixmap(scaled)
                return

        # Изображение не выбрано / файл не найден
        name = os.path.basename(path) if path else ''
        hint = f"Файл не найден:\n{name}" if path else "Изображение не выбрано"
        self._label.setPixmap(QPixmap())
        self._label.setText(f"🖼\n{hint}")
        self._label.setStyleSheet("font-size:12px; color:#9da8b7;")

    def refresh(self):
        self._apply_settings()
