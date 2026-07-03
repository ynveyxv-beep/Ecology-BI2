# widgets/dashboard/text_widget.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy

from widgets.dashboard.base_widget import BaseDashboardWidget


class TextWidget(BaseDashboardWidget):
    """Виджет для отображения произвольного текста."""

    def __init__(self, settings: dict = None, parent=None):
        # ВАЖНО: инициализируем _label до super().__init__(),
        # потому что BaseDashboardWidget.__init__ вызывает _apply_settings().
        self._label = None
        super().__init__(settings, parent)

        if self._label is None:
            self._label = QLabel()
            self._label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            self._label.setWordWrap(True)
            self._label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self._label.setTextFormat(Qt.RichText)
            self._content_layout.addWidget(self._label)

        self._apply_settings()

    def _apply_settings(self):
        """Применяет настройки."""
        if self._label is None:
            return

        content  = self._settings.get('content', '')
        size     = int(self._settings.get('font_size', 14))
        bold     = self._settings.get('bold', False)
        italic   = self._settings.get('italic', False)
        align    = self._settings.get('align', 'left')
        color    = self._settings.get('color', '#e8edf2')   # светлый по умолчанию
        bg_color = self._settings.get('bg_color', 'transparent')

        weight = 'bold'   if bold   else 'normal'
        style  = 'italic' if italic else 'normal'

        # Выравнивание Qt
        qt_align = {
            'left':   Qt.AlignLeft | Qt.AlignTop,
            'center': Qt.AlignCenter,
            'right':  Qt.AlignRight | Qt.AlignTop,
        }.get(align, Qt.AlignLeft | Qt.AlignTop)
        self._label.setAlignment(qt_align)

        css_bg = f'background:{bg_color};' if bg_color and bg_color != 'transparent' else 'background:transparent;'
        self._label.setStyleSheet(
            f"font-size:{size}px; font-weight:{weight}; font-style:{style};"
            f" color:{color}; {css_bg} padding:4px;"
        )
        self._label.setText(content or '<span style="opacity:0.4">Текст…</span>')

    def refresh(self):
        self._apply_settings()
