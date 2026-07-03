# ui/widget_palette.py
"""
Боковая палитра виджетов — тёмная природная тема.
Каждый элемент можно перетащить (drag & drop) на ячейку сетки,
либо кликнуть — тогда откроется диалог создания виджета.
"""

from PySide6.QtCore import Qt, Signal, QMimeData, QPoint
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea
from PySide6.QtGui import QDrag, QPixmap, QPainter

from ui.theme import (
    BG_PANEL, BG_CARD, BG_HOVER, BG_DARK,
    BORDER, BORDER_LT, BORDER_ACC,
    TEXT_PRI, TEXT_MUT, ACCENT, scrollbar_style
)

MIME_WIDGET_TYPE = "application/x-dashboard-widget-type"

PALETTE_ITEMS = [
    ('kpi',   '📊', 'Число / KPI',  ACCENT),
    ('chart', '📈', 'График',       '#5BA3D9'),
    ('table', '📋', 'Таблица',      '#C8A84B'),
    ('map',   '🗺',  'Карта',        '#4ECDC4'),
    ('text',  '📝', 'Текст',        '#9B72CF'),
    ('image', '🖼',  'Изображение',  '#E07070'),
]


class PaletteItem(QFrame):
    """Один перетаскиваемый элемент палитры."""

    clicked = Signal(str)

    def __init__(self, key: str, icon: str, title: str, accent: str, parent=None):
        super().__init__(parent)
        self._key        = key
        self._accent     = accent
        self._drag_start = None

        self.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 6px;
            }}
            QFrame:hover {{
                border-color: {accent};
                background: {BG_HOVER};
            }}
        """)
        self.setCursor(Qt.OpenHandCursor)
        self.setFixedHeight(68)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 8, 4, 8)
        lay.setSpacing(4)
        lay.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size:22px; background:transparent; border:none;")
        lay.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet(
            f"font-size:10px; font-weight:600; color:{TEXT_PRI}; background:transparent; border:none;"
        )
        lay.addWidget(title_lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton) or self._drag_start is None:
            return
        if (event.position().toPoint() - self._drag_start).manhattanLength() < 8:
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(MIME_WIDGET_TYPE, self._key.encode('utf-8'))
        drag.setMimeData(mime)

        pix = QPixmap(self.size())
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setOpacity(0.7)
        self.render(painter)
        painter.end()
        drag.setPixmap(pix)
        drag.setHotSpot(event.position().toPoint())
        drag.exec(Qt.CopyAction)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            delta = 0
            if self._drag_start:
                delta = (event.position().toPoint() - self._drag_start).manhattanLength()
            if delta < 8:
                self.clicked.emit(self._key)
        self._drag_start = None
        super().mouseReleaseEvent(event)


class WidgetPalette(QWidget):
    """Левая боковая панель с типами виджетов."""

    widget_type_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(114)
        self.setStyleSheet(
            f"background:{BG_PANEL}; border-right:1px solid {BORDER};"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Заголовок
        hdr = QWidget()
        hdr.setStyleSheet(f"background:{BG_DARK}; border-bottom:1px solid {BORDER};")
        hdr_lay = QVBoxLayout(hdr)
        hdr_lay.setContentsMargins(8, 10, 8, 10)
        lbl = QLabel("БЛОКИ")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            f"font-size:9px; font-weight:bold; letter-spacing:1.5px; color:{TEXT_MUT};"
        )
        hdr_lay.addWidget(lbl)
        root.addWidget(hdr)

        # Прокручиваемый список
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"QScrollArea {{ background:transparent; border:none; }}{scrollbar_style()}"
        )

        items_w = QWidget()
        items_w.setStyleSheet("background:transparent;")
        items_lay = QVBoxLayout(items_w)
        items_lay.setContentsMargins(8, 10, 8, 10)
        items_lay.setSpacing(6)

        for key, icon, title, accent in PALETTE_ITEMS:
            item = PaletteItem(key, icon, title, accent)
            item.clicked.connect(self.widget_type_clicked.emit)
            items_lay.addWidget(item)

        items_lay.addStretch()

        tip = QLabel("Перетащите\nна холст")
        tip.setAlignment(Qt.AlignCenter)
        tip.setWordWrap(True)
        tip.setStyleSheet(f"font-size:9px; color:{TEXT_MUT}; margin-top:4px;")
        items_lay.addWidget(tip)

        scroll.setWidget(items_w)
        root.addWidget(scroll, 1)
