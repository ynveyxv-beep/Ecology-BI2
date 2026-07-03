# widgets/dialogs/widget_creation_dialog.py
"""
Диалог добавления блока на дашборд.
Тёмная природная тема, 7 видов графиков, настройки текста/изображения/карты.
"""

import os
import math
from PySide6.QtCore import Qt, Signal, QByteArray, QUrl
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QColorDialog,
    QScrollArea, QFrame, QSizePolicy, QCheckBox, QFileDialog,
    QListWidget, QListWidgetItem, QPlainTextEdit, QSlider
)
from PySide6.QtGui import QColor, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    _HAS_WEBENGINE = True
except ImportError:
    _HAS_WEBENGINE = False

from ui.theme import (
    BG_DARK, BG_CARD, BG_HOVER, BG_ACTIVE, BG_PANEL,
    BORDER, BORDER_LT, BORDER_ACC,
    TEXT_PRI, TEXT_SEC, TEXT_MUT,
    ACCENT, ACCENT_DARK, ACCENT_GLOW, ACCENT_RED,
    scrollbar_style
)
from widgets.dialogs.marker_editor_dialog import MarkerEditorDialog

# ─── Источники данных ─────────────────────────────────────────────────────────

KPI_CHOICES = [
    ('total',       'Всего обращений'),
    ('done',        'Выполнено'),
    ('in_progress', 'В работе'),
    ('pct_done',    '% выполнения'),
    ('omsu_count',  'Количество районов'),
    ('period',      'Период данных'),
]

CHART_CHOICES = [
    ('by_category',   'По видам нарушений'),
    ('by_omsu',       'По районам (ОМСУ)'),
    ('by_mro',        'По МРО'),
    ('time_series_D', 'Динамика по дням'),
    ('time_series_W', 'Динамика по неделям'),
    ('none',          'Демо-данные (без файла)'),
]

TABLE_CHOICES = [
    ('by_category', 'По видам нарушений'),
    ('by_omsu',     'По районам (ОМСУ)'),
    ('by_mro',      'По МРО'),
    ('none',        'Демо-данные (без файла)'),
]

CHART_STYLES = [
    ('bar',     'Столбцы'),
    ('line',    'Линия'),
    ('area',    'Площадь'),
    ('radar',   'Паутина'),
    ('scatter', 'Точки'),
    ('heatmap', 'Тепловая'),
    ('treemap', 'Дерево'),
]

IMAGE_FIT_MODES = [
    ('contain', 'По размеру'),
    ('cover',   'Заполнить'),
    ('fill',    'Растянуть'),
    ('center',  'По центру'),
]

# ─── Вспомогательные стили ───────────────────────────────────────────────────

_LABEL_STYLE = f"font-size:12px; font-weight:600; color:{TEXT_SEC}; background:transparent;"

_COMBO_STYLE = f"""
    QComboBox {{
        background: {BG_CARD}; color: {TEXT_PRI};
        border: 1px solid {BORDER}; border-radius: 6px;
        padding: 5px 10px; font-size: 12px; min-height: 28px;
    }}
    QComboBox:hover  {{ border-color: {BORDER_LT}; }}
    QComboBox:focus  {{ border-color: {BORDER_ACC}; }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QComboBox QAbstractItemView {{
        background: {BG_PANEL}; color: {TEXT_PRI};
        border: 1px solid {BORDER_ACC}; border-radius: 6px;
        selection-background-color: {BG_ACTIVE};
        selection-color: {ACCENT}; outline: 0; padding: 4px;
    }}
    QComboBox QAbstractItemView::item {{ min-height:26px; padding:0 8px; border-radius:3px; }}
    QComboBox QAbstractItemView::item:hover {{ background:{BG_HOVER}; }}
"""
_LINEEDIT_STYLE = f"""
    QLineEdit {{
        background: {BG_CARD}; color: {TEXT_PRI};
        border: 1px solid {BORDER}; border-radius: 6px;
        padding: 5px 10px; font-size: 12px; min-height: 28px;
    }}
    QLineEdit:focus {{ border-color: {BORDER_ACC}; }}
"""
_SPINBOX_STYLE = f"""
    QSpinBox {{
        background: {BG_CARD}; color: {TEXT_PRI};
        border: 1px solid {BORDER}; border-radius: 6px;
        padding: 4px 8px; font-size: 12px; min-height: 28px;
    }}
    QSpinBox:focus {{ border-color: {BORDER_ACC}; }}
"""
_CHECK_STYLE = f"""
    QCheckBox {{ color: {TEXT_PRI}; font-size: 12px; spacing: 6px; background:transparent; }}
    QCheckBox::indicator {{
        width:16px; height:16px;
        border:1px solid {BORDER_LT}; border-radius:3px;
        background:{BG_CARD};
    }}
    QCheckBox::indicator:checked {{ background:{ACCENT_DARK}; border-color:{ACCENT}; }}
"""
_TEXTEDIT_STYLE = f"""
    QPlainTextEdit {{
        background: {BG_CARD}; color: {TEXT_PRI};
        border: 1px solid {BORDER}; border-radius: 6px;
        padding: 5px 8px; font-size: 12px;
    }}
    QPlainTextEdit:focus {{ border-color: {BORDER_ACC}; }}
"""
_SLIDER_STYLE = f"""
    QSlider::groove:horizontal {{
        height: 4px; background: {BORDER}; border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        width: 14px; height: 14px; margin: -5px 0;
        background: {ACCENT}; border-radius: 7px;
    }}
    QSlider::sub-page:horizontal {{
        background: {ACCENT_DARK}; border-radius: 2px;
    }}
"""

# ─── SVG-иконки для карточек типов ──────────────────────────────────────────

_SVG_KPI = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 52'>
  <rect width='64' height='52' rx='5' fill='#162616'/>
  <text x='32' y='30' text-anchor='middle' font-family='Arial,sans-serif'
        font-size='26' font-weight='bold' fill='#4ADE80'>42</text>
  <text x='32' y='44' text-anchor='middle' font-family='Arial,sans-serif'
        font-size='7' fill='#5A8A5A'>показатель</text>
</svg>"""

_SVG_CHART = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 52'>
  <rect width='64' height='52' rx='5' fill='#162616'/>
  <line x1='10' y1='5' x2='10' y2='44' stroke='#2D4A2D' stroke-width='1'/>
  <line x1='10' y1='44' x2='60' y2='44' stroke='#2D4A2D' stroke-width='1'/>
  <rect x='12' y='32' width='8' height='12' rx='1' fill='#4ADE80' opacity='0.55'/>
  <rect x='22' y='20' width='8' height='24' rx='1' fill='#4ADE80' opacity='0.75'/>
  <rect x='32' y='26' width='8' height='18' rx='1' fill='#4ADE80' opacity='0.65'/>
  <rect x='42' y='12' width='8' height='32' rx='1' fill='#4ADE80' opacity='0.90'/>
  <rect x='52' y='22' width='6' height='22' rx='1' fill='#4ADE80' opacity='0.70'/>
</svg>"""

_SVG_TABLE = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 52'>
  <rect width='64' height='52' rx='5' fill='#162616'/>
  <rect x='5' y='7' width='54' height='9' rx='2' fill='#2D4A2D'/>
  <line x1='5' y1='24' x2='59' y2='24' stroke='#2D4A2D' stroke-width='0.8'/>
  <line x1='5' y1='33' x2='59' y2='33' stroke='#2D4A2D' stroke-width='0.8'/>
  <line x1='5' y1='42' x2='59' y2='42' stroke='#2D4A2D' stroke-width='0.8'/>
  <line x1='26' y1='7' x2='26' y2='44' stroke='#2D4A2D' stroke-width='0.8'/>
  <line x1='44' y1='7' x2='44' y2='44' stroke='#2D4A2D' stroke-width='0.8'/>
  <rect x='46' y='26' width='11' height='5' rx='1' fill='#4ADE80' opacity='0.45'/>
</svg>"""

_SVG_TEXT = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 52'>
  <rect width='64' height='52' rx='5' fill='#162616'/>
  <rect x='8' y='10' width='30' height='6' rx='2' fill='#4ADE80' opacity='0.75'/>
  <rect x='8' y='22' width='48' height='4' rx='2' fill='#3A5A3A'/>
  <rect x='8' y='30' width='42' height='4' rx='2' fill='#3A5A3A'/>
  <rect x='8' y='38' width='34' height='4' rx='2' fill='#3A5A3A'/>
</svg>"""

_SVG_IMAGE = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 52'>
  <rect width='64' height='52' rx='5' fill='#162616'/>
  <rect x='6' y='6' width='52' height='40' rx='4' fill='#0D1A0D' stroke='#2D4A2D' stroke-width='1'/>
  <circle cx='18' cy='18' r='5' fill='#4ADE80' opacity='0.45'/>
  <polygon points='6,46 22,30 32,38 44,22 58,46' fill='#4ADE80' opacity='0.22'/>
</svg>"""

_SVG_MAP = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 52'>
  <rect width='64' height='52' rx='5' fill='#162616'/>
  <line x1='6' y1='13' x2='58' y2='13' stroke='#2D4A2D' stroke-width='0.7'/>
  <line x1='6' y1='26' x2='58' y2='26' stroke='#2D4A2D' stroke-width='0.7'/>
  <line x1='6' y1='39' x2='58' y2='39' stroke='#2D4A2D' stroke-width='0.7'/>
  <line x1='17' y1='5' x2='17' y2='47' stroke='#2D4A2D' stroke-width='0.7'/>
  <line x1='32' y1='5' x2='32' y2='47' stroke='#2D4A2D' stroke-width='0.7'/>
  <line x1='47' y1='5' x2='47' y2='47' stroke='#2D4A2D' stroke-width='0.7'/>
  <circle cx='32' cy='22' r='8' fill='#4ADE80' opacity='0.85'/>
  <circle cx='32' cy='22' r='3' fill='#0D1A0D'/>
  <line x1='32' y1='30' x2='32' y2='40' stroke='#4ADE80' stroke-width='2.5' stroke-linecap='round' opacity='0.65'/>
</svg>"""

_SVG_GAUGE = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 52'>
  <rect width='64' height='52' rx='5' fill='#162616'/>
  <path d='M 10 44 A 22 22 0 0 1 54 44' fill='none' stroke='#2D4A2D' stroke-width='6' stroke-linecap='round'/>
  <path d='M 10 44 A 22 22 0 0 1 42 24' fill='none' stroke='#4ADE80' stroke-width='6' stroke-linecap='round'/>
  <line x1='32' y1='44' x2='23' y2='28' stroke='#FFFFFF' stroke-width='2' stroke-linecap='round'/>
  <circle cx='32' cy='44' r='4' fill='#4ADE80'/>
  <text x='32' y='14' text-anchor='middle' font-family='Arial,sans-serif' font-size='9' fill='#5A8A5A'>68%</text>
</svg>"""

_SVG_PROGRESS = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 52'>
  <rect width='64' height='52' rx='5' fill='#162616'/>
  <rect x='6' y='10' width='52' height='7' rx='3.5' fill='#2D4A2D'/>
  <rect x='6' y='10' width='38' height='7' rx='3.5' fill='#4ADE80' opacity='0.85'/>
  <rect x='6' y='23' width='52' height='7' rx='3.5' fill='#2D4A2D'/>
  <rect x='6' y='23' width='22' height='7' rx='3.5' fill='#4ADE80' opacity='0.60'/>
  <rect x='6' y='36' width='52' height='7' rx='3.5' fill='#2D4A2D'/>
  <rect x='6' y='36' width='44' height='7' rx='3.5' fill='#4ADE80' opacity='0.75'/>
</svg>"""

_SVG_PIVOT = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 52'>
  <rect width='64' height='52' rx='5' fill='#162616'/>
  <rect x='4' y='5' width='24' height='9' rx='2' fill='#2D4A2D'/>
  <rect x='30' y='5' width='16' height='9' rx='2' fill='#2D4A2D'/>
  <rect x='48' y='5' width='12' height='9' rx='2' fill='#2D4A2D'/>
  <rect x='4' y='16' width='24' height='9' rx='1' fill='#1A2A1A' stroke='#2D4A2D' stroke-width='0.5'/>
  <rect x='30' y='16' width='16' height='9' rx='1' fill='#1E311E'/>
  <rect x='48' y='16' width='12' height='9' rx='1' fill='#1E311E'/>
  <rect x='4' y='27' width='24' height='9' rx='1' fill='#1A2A1A' stroke='#2D4A2D' stroke-width='0.5'/>
  <rect x='30' y='27' width='16' height='9' rx='1' fill='#1E311E'/>
  <rect x='48' y='27' width='12' height='9' rx='1' fill='#4ADE80' opacity='0.50'/>
  <rect x='4' y='38' width='24' height='9' rx='1' fill='#1A2A1A' stroke='#2D4A2D' stroke-width='0.5'/>
  <text x='38' y='23' text-anchor='middle' font-family='Arial' font-size='6' fill='#5A8A5A'>145</text>
  <text x='54' y='23' text-anchor='middle' font-family='Arial' font-size='6' fill='#5A8A5A'>87</text>
  <text x='38' y='34' text-anchor='middle' font-family='Arial' font-size='6' fill='#5A8A5A'>230</text>
  <text x='54' y='34' text-anchor='middle' font-family='Arial' font-size='6' fill='#4ADE80'>312</text>
</svg>"""


# ─── Карточка выбора типа ─────────────────────────────────────────────────────

class TypeCard(QFrame):
    clicked = Signal(str)

    _NORMAL  = f"QFrame{{background:{BG_CARD};border:2px solid {BORDER};border-radius:6px;}}" \
               f"QFrame:hover{{border-color:{BORDER_LT};background:{BG_HOVER};}}"
    _ACTIVE  = f"QFrame{{background:{BG_ACTIVE};border:2px solid {BORDER_ACC};border-radius:6px;}}"

    def __init__(self, key: str, icon: str, title: str, hint: str, parent=None,
                 svg_data: str = None):
        super().__init__(parent)
        self._key = key
        self._selected = False
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(self._NORMAL)
        self.setMinimumWidth(90)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 8, 6, 8)
        lay.setSpacing(4)
        lay.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("background:transparent; border:none;")
        if svg_data:
            pix = QPixmap(60, 48)
            pix.fill(Qt.transparent)
            renderer = QSvgRenderer(QByteArray(svg_data.strip().encode('utf-8')))
            if renderer.isValid():
                painter = QPainter(pix)
                painter.setRenderHint(QPainter.Antialiasing)
                renderer.render(painter)
                painter.end()
                icon_lbl.setPixmap(pix)
            else:
                icon_lbl.setText(icon)
                icon_lbl.setStyleSheet("font-size:24px; background:transparent; border:none;")
        else:
            icon_lbl.setText(icon)
            icon_lbl.setStyleSheet("font-size:24px; background:transparent; border:none;")
        lay.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(
            f"font-size:11px; font-weight:bold; color:{TEXT_PRI}; background:transparent; border:none;"
        )
        lay.addWidget(title_lbl)

        hint_lbl = QLabel(hint)
        hint_lbl.setAlignment(Qt.AlignCenter)
        hint_lbl.setWordWrap(True)
        hint_lbl.setStyleSheet(
            f"font-size:10px; color:{TEXT_MUT}; background:transparent; border:none;"
        )
        lay.addWidget(hint_lbl)

    def set_selected(self, val: bool):
        self._selected = val
        self.setStyleSheet(self._ACTIVE if val else self._NORMAL)

    def mousePressEvent(self, event):
        self.clicked.emit(self._key)
        super().mousePressEvent(event)


# ─── Основной диалог ─────────────────────────────────────────────────────────

class WidgetCreationDialog(QDialog):
    widget_created = Signal(str, dict)

    _MAIN_TYPES = [
        ('kpi',   '', 'Число',        'Ключевой показатель', _SVG_KPI),
        ('chart', '', 'График',       'Диаграмма',           _SVG_CHART),
        ('table', '', 'Таблица',      'Список записей',      _SVG_TABLE),
        ('text',  '', 'Текст',        'Заголовок / абзац',   _SVG_TEXT),
        ('image', '', 'Изображение',  'Фото / логотип',      _SVG_IMAGE),
        ('map',   '', 'Карта',        'Геоданные',           _SVG_MAP),
    ]
    _EXTRA_TYPES = [
        ('gauge',    '⊙', 'Датчик',   _SVG_GAUGE),
        ('progress', '≡', 'Прогресс', _SVG_PROGRESS),
        ('pivot',    '⊞', 'Сводная',  _SVG_PIVOT),
    ]

    def __init__(self, parent=None, preset_type: str = None, datasets: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Добавить блок на дашборд")
        self.setModal(True)
        self.setMinimumSize(520, 420)
        self.resize(560, 660)

        self._current_type     = preset_type or 'kpi'
        self._kpi_color        = ACCENT_DARK
        self._chart_color      = ACCENT
        self._text_color       = TEXT_PRI
        self._text_bg_color    = 'transparent'
        self._image_path       = ''
        self._advanced_visible = False
        self._datasets         = datasets or {}
        self._chart_style_key  = 'bar'
        self._geo_lat          = None
        self._geo_lon          = None
        self._territories      = []   # список полигонов [{lat,lon},...]

        self.setStyleSheet(f"""
            QDialog {{ background:{BG_DARK}; }}
            QLabel  {{ color:{TEXT_PRI}; background:transparent; }}
            {_COMBO_STYLE}
            {_LINEEDIT_STYLE}
            {_SPINBOX_STYLE}
            {_CHECK_STYLE}
            {_TEXTEDIT_STYLE}
            {_SLIDER_STYLE}
            QScrollArea {{ background:transparent; border:none; }}
            {scrollbar_style()}
        """)

        self._build_ui()
        self._select_type(self._current_type)

    # ─── Построение UI ─────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(10)

        # ── Заголовок (фиксированный) ─────────────────────────────────────
        title = QLabel("Что добавить на дашборд?")
        title.setStyleSheet(f"font-size:15px; font-weight:bold; color:{TEXT_PRI};")
        root.addWidget(title)

        # ── Карточки основных типов: 2 ряда по 3 (фиксированные) ─────────
        self._type_cards = {}
        for row_slice in (self._MAIN_TYPES[:3], self._MAIN_TYPES[3:]):
            cards_row = QHBoxLayout()
            cards_row.setSpacing(6)
            for key, icon, label, hint, svg in row_slice:
                card = TypeCard(key, icon, label, hint, svg_data=svg)
                card.clicked.connect(self._select_type)
                cards_row.addWidget(card)
                self._type_cards[key] = card
            root.addLayout(cards_row)

        # ── Дополнительные типы (фиксированные) ──────────────────────────
        extras_row = QHBoxLayout()
        extras_row.setSpacing(6)
        extras_lbl = QLabel("Другое:")
        extras_lbl.setStyleSheet(f"color:{TEXT_MUT}; font-size:11px;")
        extras_row.addWidget(extras_lbl)
        _extra_btn_style = f"""
            QPushButton {{
                background:{BG_CARD}; border:1px solid {BORDER};
                border-radius:4px; padding:3px 10px;
                font-size:11px; color:{TEXT_SEC};
            }}
            QPushButton:hover   {{ background:{BG_HOVER}; border-color:{BORDER_LT}; }}
            QPushButton:checked {{ background:{BG_ACTIVE}; border-color:{BORDER_ACC}; color:{ACCENT}; }}
        """
        for key, icon, label, _svg in self._EXTRA_TYPES:
            btn = QPushButton(f"{icon} {label}")
            btn.setCheckable(True)
            btn.setStyleSheet(_extra_btn_style)
            btn.clicked.connect(lambda _, k=key: self._select_type(k))
            extras_row.addWidget(btn)
            self._type_cards[key] = btn
        extras_row.addStretch()
        root.addLayout(extras_row)

        # ── Превью (фиксированный) ────────────────────────────────────────
        self._preview = QLabel()
        self._preview.setAlignment(Qt.AlignCenter)
        self._preview.setFixedHeight(148)
        self._preview.setStyleSheet(
            f"background:{BG_CARD}; border:1px solid {BORDER}; border-radius:8px;"
        )
        root.addWidget(self._preview)

        # ── Прокручиваемая область: поля + дополнительные настройки ──────
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background:transparent;")
        sc_lay = QVBoxLayout(scroll_content)
        sc_lay.setContentsMargins(0, 0, 8, 0)
        sc_lay.setSpacing(8)

        fields_w = QWidget()
        fl = QVBoxLayout(fields_w)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(8)

        # Выбор датасета
        self._dataset_label = QLabel("Датасет:")
        self._dataset_label.setStyleSheet(_LABEL_STYLE)
        fl.addWidget(self._dataset_label)
        self._dataset_combo = QComboBox()
        self._dataset_combo.addItem("— не выбран —", "")
        for name in self._datasets.keys():
            self._dataset_combo.addItem(f"📊 {name}", name)
        self._dataset_combo.currentIndexChanged.connect(self._on_dataset_changed)
        fl.addWidget(self._dataset_combo)
        if not self._datasets:
            self._dataset_label.hide()
            self._dataset_combo.hide()

        # Источник данных (KPI/Chart/Table)
        self._source_label = QLabel("Что показать:")
        self._source_label.setStyleSheet(_LABEL_STYLE)
        fl.addWidget(self._source_label)
        self._source_combo = QComboBox()
        self._source_combo.currentIndexChanged.connect(self._update_preview)
        fl.addWidget(self._source_combo)

        # ── Стиль графика ────────────────────────────────────────────────
        self._chart_style_row = QWidget()
        cs_lay = QVBoxLayout(self._chart_style_row)
        cs_lay.setContentsMargins(0, 0, 0, 0)
        cs_lay.setSpacing(4)
        cs_lbl = QLabel("Вид графика:")
        cs_lbl.setStyleSheet(_LABEL_STYLE)
        cs_lay.addWidget(cs_lbl)
        row1 = QHBoxLayout(); row1.setSpacing(5)
        row2 = QHBoxLayout(); row2.setSpacing(5)
        self._chart_style_btns = {}
        _cs_btn = f"""
            QPushButton {{
                background:{BG_CARD}; border:1px solid {BORDER};
                border-radius:4px; padding:5px 10px;
                font-size:11px; color:{TEXT_SEC};
            }}
            QPushButton:hover   {{ background:{BG_HOVER}; border-color:{BORDER_LT}; }}
            QPushButton:checked {{ background:{BG_ACTIVE}; border-color:{BORDER_ACC};
                                   color:{ACCENT}; font-weight:bold; }}
        """
        for _i, (_k, _lbl) in enumerate(CHART_STYLES):
            _btn = QPushButton(_lbl)
            _btn.setCheckable(True)
            _btn.setStyleSheet(_cs_btn)
            _btn.clicked.connect(lambda _, k=_k: self._select_chart_style(k))
            self._chart_style_btns[_k] = _btn
            (row1 if _i < 4 else row2).addWidget(_btn)
        row1.addStretch(); row2.addStretch()
        cs_lay.addLayout(row1); cs_lay.addLayout(row2)
        fl.addWidget(self._chart_style_row)
        self._chart_style_row.hide()
        self._chart_style_key = 'bar'
        self._chart_style_btns['bar'].setChecked(True)

        # ── KPI: переключатель режима ────────────────────────────────────
        self._kpi_mode_row = QWidget()
        km_lay = QHBoxLayout(self._kpi_mode_row)
        km_lay.setContentsMargins(0, 0, 0, 0)
        km_lay.setSpacing(4)
        _toggle = f"""
            QPushButton {{
                background:{BG_CARD}; border:1px solid {BORDER};
                border-radius:5px; padding:5px 14px;
                font-size:12px; color:{TEXT_SEC};
            }}
            QPushButton:hover {{ background:{BG_HOVER}; border-color:{BORDER_LT}; }}
            QPushButton:checked {{
                background:{BG_ACTIVE}; border-color:{BORDER_ACC};
                color:{ACCENT}; font-weight:bold;
            }}
        """
        self._kpi_manual_btn = QPushButton("📌 Своё значение")
        self._kpi_manual_btn.setCheckable(True)
        self._kpi_manual_btn.setChecked(True)
        self._kpi_manual_btn.setStyleSheet(_toggle)
        self._kpi_manual_btn.clicked.connect(lambda: self._set_kpi_mode('manual'))
        self._kpi_dataset_btn = QPushButton("📊 Из датасета")
        self._kpi_dataset_btn.setCheckable(True)
        self._kpi_dataset_btn.setStyleSheet(_toggle)
        self._kpi_dataset_btn.clicked.connect(lambda: self._set_kpi_mode('dataset'))
        km_lay.addWidget(self._kpi_manual_btn)
        km_lay.addWidget(self._kpi_dataset_btn)
        km_lay.addStretch()
        fl.addWidget(self._kpi_mode_row)
        self._kpi_mode_row.hide()

        # ── KPI: выбор столбца и агрегации (режим «Из датасета») ────────────
        self._kpi_col_row = QWidget()
        kcr_lay = QVBoxLayout(self._kpi_col_row)
        kcr_lay.setContentsMargins(0, 0, 0, 0)
        kcr_lay.setSpacing(4)

        kc_lbl = QLabel("Столбец:")
        kc_lbl.setStyleSheet(_LABEL_STYLE)
        kcr_lay.addWidget(kc_lbl)
        self._kpi_column_combo = QComboBox()
        self._kpi_column_combo.currentIndexChanged.connect(self._update_preview)
        kcr_lay.addWidget(self._kpi_column_combo)

        agg_lbl = QLabel("Агрегация:")
        agg_lbl.setStyleSheet(_LABEL_STYLE)
        kcr_lay.addWidget(agg_lbl)
        self._kpi_agg_combo = QComboBox()
        for _av, _al in [
            ('value',  'Значение (без агрегации)'),
            ('sum',    'Сумма'),
            ('avg',    'Среднее'),
            ('median', 'Медиана'),
            ('count',  'Количество строк'),
            ('unique', 'Уникальных значений'),
            ('max',    'Максимум'),
            ('min',    'Минимум'),
            ('first',  'Первое значение'),
            ('last',   'Последнее значение'),
        ]:
            self._kpi_agg_combo.addItem(_al, _av)
        self._kpi_agg_combo.currentIndexChanged.connect(self._update_preview)
        kcr_lay.addWidget(self._kpi_agg_combo)

        fl.addWidget(self._kpi_col_row)
        self._kpi_col_row.hide()

        # KPI manual fields
        self._manual_label = QLabel("Значение:")
        self._manual_label.setStyleSheet(_LABEL_STYLE)
        self._manual_value = QLineEdit()
        self._manual_value.setPlaceholderText("Например: 1 234")
        self._manual_value.textChanged.connect(self._update_preview)
        self._manual_label.hide(); self._manual_value.hide()
        fl.addWidget(self._manual_label); fl.addWidget(self._manual_value)

        self._kpi_unit_label = QLabel("Единица измерения:")
        self._kpi_unit_label.setStyleSheet(_LABEL_STYLE)
        self._kpi_unit_edit = QLineEdit()
        self._kpi_unit_edit.setPlaceholderText("мкг/м³, шт., %, т/год…")
        self._kpi_unit_edit.textChanged.connect(self._update_preview)
        self._kpi_unit_label.hide(); self._kpi_unit_edit.hide()
        fl.addWidget(self._kpi_unit_label); fl.addWidget(self._kpi_unit_edit)

        # ── Текстовый блок ───────────────────────────────────────────────
        self._text_settings_w = self._build_text_settings_widget()
        fl.addWidget(self._text_settings_w)
        self._text_settings_w.hide()

        # ── Изображение ──────────────────────────────────────────────────
        self._image_settings_w = self._build_image_settings_widget()
        fl.addWidget(self._image_settings_w)
        self._image_settings_w.hide()

        # ── Карта: адрес ─────────────────────────────────────────────────
        self._map_settings_w = self._build_map_settings_widget()
        fl.addWidget(self._map_settings_w)
        self._map_settings_w.hide()

        # ── Заглушка для новых типов (датчик / прогресс / сводная) ──────
        self._stub_settings_w = QWidget()
        stub_lay = QVBoxLayout(self._stub_settings_w)
        stub_lay.setContentsMargins(0, 4, 0, 0)
        stub_lay.setSpacing(6)
        self._stub_label = QLabel("Значение / источник:")
        self._stub_label.setStyleSheet(_LABEL_STYLE)
        stub_lay.addWidget(self._stub_label)
        self._stub_value_edit = QLineEdit()
        self._stub_value_edit.setPlaceholderText("Введите значение или оставьте пустым")
        self._stub_value_edit.textChanged.connect(self._update_preview)
        stub_lay.addWidget(self._stub_value_edit)
        fl.addWidget(self._stub_settings_w)
        self._stub_settings_w.hide()

        # Подпись карточки
        self._title_lbl_widget = QLabel("Подпись карточки:")
        self._title_lbl_widget.setStyleSheet(_LABEL_STYLE)
        fl.addWidget(self._title_lbl_widget)
        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("Оставьте пустым — подберём автоматически")
        self._title_edit.textChanged.connect(self._update_preview)
        fl.addWidget(self._title_edit)

        sc_lay.addWidget(fields_w)

        # Кнопка «Дополнительно»
        self._adv_toggle = QPushButton("▸  Дополнительные настройки")
        self._adv_toggle.setStyleSheet(f"""
            QPushButton {{
                background:transparent; border:none;
                color:{ACCENT}; font-size:12px; text-align:left; padding:2px 0;
            }}
            QPushButton:hover {{ color:{ACCENT_GLOW}; }}
        """)
        self._adv_toggle.clicked.connect(self._toggle_advanced)
        sc_lay.addWidget(self._adv_toggle)

        self._adv_panel = self._build_advanced_panel()
        self._adv_panel.hide()
        sc_lay.addWidget(self._adv_panel)
        sc_lay.addStretch()

        # Прокручиваемая область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_content)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root.addWidget(scroll, 1)

        # ── Кнопка «Добавить» (фиксированная внизу) ──────────────────────
        self._add_btn = QPushButton("✓   Добавить на дашборд")
        self._add_btn.setFixedHeight(42)
        self._add_btn.setStyleSheet(f"""
            QPushButton {{
                background:{ACCENT_DARK}; color:{TEXT_PRI};
                border:none; border-radius:6px;
                font-size:14px; font-weight:bold;
            }}
            QPushButton:hover   {{ background:{ACCENT}; color:#0F1A0F; }}
            QPushButton:pressed {{ background:{ACCENT_DARK}; }}
        """)
        self._add_btn.clicked.connect(self._on_add)
        root.addWidget(self._add_btn)

    # ─── Текстовый блок: поля ──────────────────────────────────────────────

    def _build_text_settings_widget(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        lay.addWidget(_lbl("Содержимое текста:"))
        self._text_content = QPlainTextEdit()
        self._text_content.setPlaceholderText("Введите текст, заголовок, описание…")
        self._text_content.setMaximumHeight(80)
        self._text_content.textChanged.connect(self._update_preview)
        lay.addWidget(self._text_content)

        fmt_row = QHBoxLayout(); fmt_row.setSpacing(6)
        fmt_row.addWidget(_lbl("Размер:", small=True))
        self._text_font_size = QSpinBox()
        self._text_font_size.setRange(8, 72); self._text_font_size.setValue(14)
        self._text_font_size.setFixedWidth(64)
        self._text_font_size.valueChanged.connect(self._update_preview)
        fmt_row.addWidget(self._text_font_size)

        _fb = f"""QPushButton{{background:{BG_CARD};border:1px solid {BORDER};border-radius:4px;
            padding:3px 10px;font-size:12px;color:{TEXT_SEC};min-width:32px;}}
            QPushButton:hover{{background:{BG_HOVER};border-color:{BORDER_LT};}}
            QPushButton:checked{{background:{BG_ACTIVE};border-color:{BORDER_ACC};color:{ACCENT};}}"""
        self._text_bold_btn = QPushButton("Ж"); self._text_bold_btn.setCheckable(True)
        self._text_bold_btn.setStyleSheet(_fb + "QPushButton{font-weight:bold;}")
        self._text_bold_btn.clicked.connect(self._update_preview)
        self._text_italic_btn = QPushButton("К"); self._text_italic_btn.setCheckable(True)
        self._text_italic_btn.setStyleSheet(_fb + "QPushButton{font-style:italic;}")
        self._text_italic_btn.clicked.connect(self._update_preview)
        fmt_row.addWidget(self._text_bold_btn); fmt_row.addWidget(self._text_italic_btn)
        fmt_row.addStretch()
        lay.addLayout(fmt_row)

        align_row = QHBoxLayout(); align_row.setSpacing(4)
        align_row.addWidget(_lbl("Выравнивание:", small=True))
        self._text_align_btns = {}
        for key, label in [('left', '⬅'), ('center', '⬛'), ('right', '➡')]:
            btn = QPushButton(label); btn.setCheckable(True); btn.setFixedWidth(36)
            btn.setStyleSheet(_fb)
            btn.clicked.connect(lambda _, k=key: self._set_text_align(k))
            align_row.addWidget(btn); self._text_align_btns[key] = btn
        self._text_align_key = 'left'
        self._text_align_btns['left'].setChecked(True)
        align_row.addStretch()
        lay.addLayout(align_row)

        color_row = QHBoxLayout(); color_row.setSpacing(8)
        color_row.addWidget(_lbl("Цвет текста:", small=True))
        self._text_color_preview = _color_swatch(self._text_color)
        color_row.addWidget(self._text_color_preview)
        tc_btn = _small_btn("Выбрать"); tc_btn.clicked.connect(self._pick_text_color)
        color_row.addWidget(tc_btn)
        color_row.addSpacing(12)
        color_row.addWidget(_lbl("Фон:", small=True))
        self._text_bg_preview = _color_swatch(BG_CARD)
        color_row.addWidget(self._text_bg_preview)
        bg_btn = _small_btn("Выбрать"); bg_btn.clicked.connect(self._pick_text_bg)
        color_row.addWidget(bg_btn)
        color_row.addStretch()
        lay.addLayout(color_row)
        return w

    # ─── Изображение: поля ─────────────────────────────────────────────────

    def _build_image_settings_widget(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        lay.addWidget(_lbl("Файл изображения:"))
        file_row = QHBoxLayout(); file_row.setSpacing(6)
        self._image_path_edit = QLineEdit()
        self._image_path_edit.setPlaceholderText("Выберите PNG, JPG, BMP, SVG…")
        self._image_path_edit.setReadOnly(True)
        file_row.addWidget(self._image_path_edit)
        browse_btn = QPushButton("📂 Обзор")
        browse_btn.setFixedHeight(32)
        browse_btn.setStyleSheet(
            f"QPushButton{{background:{BG_CARD};border:1px solid {BORDER};border-radius:6px;"
            f"color:{TEXT_SEC};padding:0 12px;font-size:11px;}}"
            f"QPushButton:hover{{border-color:{BORDER_ACC};color:{ACCENT};}}"
        )
        browse_btn.clicked.connect(self._browse_image)
        file_row.addWidget(browse_btn)
        lay.addLayout(file_row)

        lay.addWidget(_lbl("Непрозрачность:"))
        op_row = QHBoxLayout(); op_row.setSpacing(8)
        self._image_opacity = QSlider(Qt.Horizontal)
        self._image_opacity.setRange(10, 100); self._image_opacity.setValue(100)
        self._image_opacity.valueChanged.connect(self._on_opacity_changed)
        op_row.addWidget(self._image_opacity)
        self._opacity_value_lbl = QLabel("100%")
        self._opacity_value_lbl.setFixedWidth(36)
        self._opacity_value_lbl.setStyleSheet(f"font-size:11px; color:{TEXT_MUT}; background:transparent;")
        op_row.addWidget(self._opacity_value_lbl)
        lay.addLayout(op_row)

        lay.addWidget(_lbl("Режим вписывания:"))
        self._image_fit_combo = QComboBox()
        for val, label in IMAGE_FIT_MODES:
            self._image_fit_combo.addItem(label, val)
        lay.addWidget(self._image_fit_combo)
        return w

    # ─── Карта: поля ───────────────────────────────────────────────────────

    def _build_map_settings_widget(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        _tb = f"""QPushButton{{background:{BG_CARD};border:1px solid {BORDER};
            border-radius:4px;padding:5px 10px;font-size:11px;color:{TEXT_SEC};}}
            QPushButton:hover{{background:{BG_HOVER};border-color:{BORDER_LT};}}
            QPushButton:checked{{background:{BG_ACTIVE};border-color:{BORDER_ACC};
            color:{ACCENT};font-weight:bold;}}"""

        # ── Адрес / центральная точка ────────────────────────────────────────
        addr_frame = QFrame()
        addr_frame.setStyleSheet(
            f"QFrame{{background:{BG_PANEL};border:1px solid {BORDER};border-radius:6px;}}"
            f"QLabel{{background:transparent;}}"
        )
        af_lay = QVBoxLayout(addr_frame)
        af_lay.setContentsMargins(10, 8, 10, 8)
        af_lay.setSpacing(5)
        af_lay.addWidget(_lbl("Адрес точки на карте:"))

        addr_grid = QHBoxLayout(); addr_grid.setSpacing(6)
        self._map_city_input = QLineEdit()
        self._map_city_input.setPlaceholderText("Город / нас. пункт")
        addr_grid.addWidget(self._map_city_input, 3)
        self._map_street_input = QLineEdit()
        self._map_street_input.setPlaceholderText("Улица")
        addr_grid.addWidget(self._map_street_input, 3)
        self._map_house_input = QLineEdit()
        self._map_house_input.setPlaceholderText("Дом")
        addr_grid.addWidget(self._map_house_input, 1)
        af_lay.addLayout(addr_grid)

        geo_row2 = QHBoxLayout(); geo_row2.setSpacing(8)
        geo_btn2 = QPushButton("🔍 Найти и добавить маркер")
        geo_btn2.setFixedHeight(28)
        geo_btn2.setStyleSheet(
            f"QPushButton{{background:{BG_CARD};border:1px solid {BORDER_ACC};"
            f"border-radius:5px;color:{ACCENT};padding:0 12px;font-size:11px;}}"
            f"QPushButton:hover{{background:{BG_ACTIVE};}}"
        )
        geo_btn2.clicked.connect(self._geocode_address)
        geo_row2.addWidget(geo_btn2)
        self._geo_result_lbl = QLabel("")
        self._geo_result_lbl.setStyleSheet(
            f"font-size:10px;color:{TEXT_MUT};background:transparent;"
        )
        self._geo_result_lbl.setWordWrap(True)
        geo_row2.addWidget(self._geo_result_lbl, 1)
        af_lay.addLayout(geo_row2)
        lay.addWidget(addr_frame)

        # ── Вид карты ────────────────────────────────────────────────────────
        lay.addWidget(_lbl("Выделение области:"))
        view_row1 = QHBoxLayout(); view_row1.setSpacing(5)
        view_row2 = QHBoxLayout(); view_row2.setSpacing(5)
        self._view_mode_btns = {}
        _modes = [
            ('point',      '📍', 'По точке',       view_row1),
            ('settlement', '🏘', 'Нас. пункт',     view_row1),
            ('district',   '🗺', 'Район',           view_row1),
            ('region',     '🌍', 'Область',         view_row2),
            ('radius',     '⭕', 'По радиусу',      view_row2),
            ('polygon',    '⬡', 'По площади',      view_row2),
        ]
        for key, icon, label, row in _modes:
            btn = QPushButton(f"{icon} {label}"); btn.setCheckable(True)
            btn.setStyleSheet(_tb)
            btn.clicked.connect(lambda _, k=key: self._set_view_mode(k))
            row.addWidget(btn); self._view_mode_btns[key] = btn
        view_row1.addStretch(); view_row2.addStretch()
        lay.addLayout(view_row1); lay.addLayout(view_row2)
        self._map_view_mode = 'point'
        self._view_mode_btns['point'].setChecked(True)

        # ── Поле радиуса (показывается только при режиме 'radius') ───────────
        self._radius_row = QFrame()
        self._radius_row.setStyleSheet(
            f"QFrame{{background:{BG_PANEL};border:1px solid {BORDER_ACC};"
            f"border-radius:5px;}}QLabel{{background:transparent;}}"
        )
        rr_lay = QHBoxLayout(self._radius_row)
        rr_lay.setContentsMargins(10, 6, 10, 6); rr_lay.setSpacing(8)
        rr_lay.addWidget(_lbl("Радиус зоны:"))
        self._area_radius_spin = QSpinBox()
        self._area_radius_spin.setRange(100, 500000)
        self._area_radius_spin.setSingleStep(500)
        self._area_radius_spin.setValue(1000)
        self._area_radius_spin.setSuffix(" м")
        self._area_radius_spin.setFixedWidth(110)
        self._area_radius_spin.setStyleSheet(
            f"QSpinBox{{background:{BG_CARD};border:1px solid {BORDER};"
            f"border-radius:4px;color:{TEXT_PRI};padding:3px 6px;font-size:12px;}}"
            f"QSpinBox::up-button,QSpinBox::down-button{{background:{BG_HOVER};border:none;width:16px;}}"
        )
        rr_lay.addWidget(self._area_radius_spin)
        _presets = [('500 м', 500), ('1 км', 1000), ('5 км', 5000),
                    ('10 км', 10000), ('50 км', 50000)]
        for plbl, pval in _presets:
            pb = QPushButton(plbl)
            pb.setFixedHeight(24)
            pb.setStyleSheet(
                f"QPushButton{{background:{BG_CARD};border:1px solid {BORDER};"
                f"border-radius:3px;color:{TEXT_SEC};padding:0 6px;font-size:10px;}}"
                f"QPushButton:hover{{border-color:{BORDER_ACC};color:{ACCENT};}}"
            )
            pb.clicked.connect(lambda _, v=pval: self._area_radius_spin.setValue(v))
            rr_lay.addWidget(pb)
        rr_lay.addStretch()
        lay.addWidget(self._radius_row)
        self._radius_row.setVisible(False)

        # ── Подсказка для режима polygon ──────────────────────────────────────
        self._polygon_hint = QLabel(
            "Нарисуйте зону на карте с помощью кнопки «Нарисовать на карте» ниже."
        )
        self._polygon_hint.setWordWrap(True)
        self._polygon_hint.setStyleSheet(
            f"font-size:10px;color:{ACCENT};background:{BG_PANEL};"
            f"border:1px solid {BORDER_ACC};border-radius:4px;padding:5px 8px;"
        )
        lay.addWidget(self._polygon_hint)
        self._polygon_hint.setVisible(False)

        # ── Стиль иконки по умолчанию ─────────────────────────────────────
        lay.addWidget(_lbl("Иконка по умолчанию:"))
        icon_row = QHBoxLayout(); icon_row.setSpacing(5)
        self._map_icon_btns = {}
        for key, label in [('pin','● Булавка'),('circle','○ Кружок'),
                            ('pulse','◎ Пульс'),('star','★ Звезда'),
                            ('flag','⚑ Флажок'),('dot','· Точка')]:
            btn = QPushButton(label); btn.setCheckable(True)
            btn.setStyleSheet(_tb)
            btn.clicked.connect(lambda _, k=key: self._set_map_icon(k))
            icon_row.addWidget(btn); self._map_icon_btns[key] = btn
        icon_row.addStretch()
        lay.addLayout(icon_row)
        self._map_icon_key = 'pin'
        self._map_icon_btns['pin'].setChecked(True)

        # ── Режим подписи по умолчанию ────────────────────────────────────
        lay.addWidget(_lbl("Подпись по умолчанию:"))
        lbl_row = QHBoxLayout(); lbl_row.setSpacing(5)
        self._map_label_btns = {}
        for key, label in [('name','Название'),('address','Адрес'),
                            ('coords','Коорд.'),('none','Без подписи')]:
            btn = QPushButton(label); btn.setCheckable(True)
            btn.setStyleSheet(_tb)
            btn.clicked.connect(lambda _, k=key: self._set_map_label_mode(k))
            lbl_row.addWidget(btn); self._map_label_btns[key] = btn
        lbl_row.addStretch()
        lay.addLayout(lbl_row)
        self._map_label_mode = 'name'
        self._map_label_btns['name'].setChecked(True)

        # ── Кнопки карты ─────────────────────────────────────────────────
        map_btn_row = QHBoxLayout(); map_btn_row.setSpacing(6)
        open_map_btn = QPushButton("🗺 Просмотр карты")
        open_map_btn.setFixedHeight(30)
        open_map_btn.setStyleSheet(
            f"QPushButton{{background:{BG_CARD};border:1px solid {BORDER};"
            f"border-radius:5px;color:{TEXT_SEC};padding:0 12px;font-size:11px;}}"
            f"QPushButton:hover{{border-color:{BORDER_ACC};color:{ACCENT};}}"
        )
        open_map_btn.clicked.connect(self._open_map_preview)
        map_btn_row.addWidget(open_map_btn)
        map_btn_row.addStretch()
        lay.addLayout(map_btn_row)

        # ── Маркеры (единый список) ───────────────────────────────────────
        sep1 = QLabel("Маркеры на карте:")
        sep1.setStyleSheet(f"font-size:11px;font-weight:600;color:{TEXT_SEC};"
                           f"background:transparent;margin-top:2px;")
        lay.addWidget(sep1)

        self._manual_markers = []
        self._marker_list = QListWidget()
        self._marker_list.setFixedHeight(90)
        self._marker_list.setStyleSheet(
            f"QListWidget{{background:{BG_CARD};border:1px solid {BORDER};border-radius:4px;"
            f"color:{TEXT_PRI};font-size:11px;}}"
            f"QListWidget::item{{padding:4px 6px;border-bottom:1px solid {BG_PANEL};}}"
            f"QListWidget::item:selected{{background:{BG_HOVER};color:{ACCENT};}}"
        )
        lay.addWidget(self._marker_list)

        mk_btns = QHBoxLayout(); mk_btns.setSpacing(4)
        for label, slot in [
            ("+ Добавить", self._add_manual_marker),
            ("✎ Изменить", self._edit_manual_marker),
            ("✕ Удалить",  self._remove_manual_marker),
        ]:
            btn = QPushButton(label)
            btn.setStyleSheet(
                f"QPushButton{{background:{BG_CARD};border:1px solid {BORDER};"
                f"border-radius:4px;color:{TEXT_SEC};padding:3px 8px;font-size:11px;}}"
                f"QPushButton:hover{{border-color:{BORDER_LT};color:{TEXT_PRI};}}"
            )
            btn.clicked.connect(slot)
            mk_btns.addWidget(btn)
        mk_btns.addStretch()
        lay.addLayout(mk_btns)

        # ── Территории ───────────────────────────────────────────────────────
        sep2 = QLabel("Выделенные территории:")
        sep2.setStyleSheet(f"font-size:11px;font-weight:600;color:{TEXT_SEC};"
                           f"background:transparent;margin-top:2px;")
        lay.addWidget(sep2)

        self._territory_list = QListWidget()
        self._territory_list.setFixedHeight(55)
        self._territory_list.setStyleSheet(
            f"QListWidget{{background:{BG_CARD};border:1px solid {BORDER};border-radius:4px;"
            f"color:{TEXT_PRI};font-size:11px;}}"
            f"QListWidget::item{{padding:3px 6px;border-bottom:1px solid {BG_PANEL};}}"
            f"QListWidget::item:selected{{background:{BG_HOVER};color:{ACCENT};}}"
        )
        lay.addWidget(self._territory_list)

        ter_btns = QHBoxLayout(); ter_btns.setSpacing(4)
        draw_btn = QPushButton("✏ Нарисовать на карте")
        draw_btn.setStyleSheet(
            f"QPushButton{{background:{BG_CARD};border:1px solid {BORDER_ACC};"
            f"border-radius:4px;color:{ACCENT};padding:3px 10px;font-size:11px;}}"
            f"QPushButton:hover{{background:{BG_ACTIVE};}}"
        )
        draw_btn.clicked.connect(self._open_map_editor)
        ter_btns.addWidget(draw_btn)
        clear_ter_btn = QPushButton("✕ Очистить")
        clear_ter_btn.setStyleSheet(
            f"QPushButton{{background:{BG_CARD};border:1px solid {BORDER};"
            f"border-radius:4px;color:{TEXT_SEC};padding:3px 8px;font-size:11px;}}"
            f"QPushButton:hover{{border-color:{BORDER_LT};color:{ACCENT_RED};}}"
        )
        clear_ter_btn.clicked.connect(self._clear_territories)
        ter_btns.addWidget(clear_ter_btn)
        ter_btns.addStretch()
        lay.addLayout(ter_btns)

        self._geo_lat = self._geo_lon = None
        return w

    def _set_view_mode(self, key: str):
        self._map_view_mode = key
        for k, b in self._view_mode_btns.items(): b.setChecked(k == key)
        if hasattr(self, '_radius_row'):
            self._radius_row.setVisible(key == 'radius')
        if hasattr(self, '_polygon_hint'):
            self._polygon_hint.setVisible(key == 'polygon')

    def _set_map_icon(self, key: str):
        self._map_icon_key = key
        for k, b in self._map_icon_btns.items(): b.setChecked(k == key)

    def _set_map_label_mode(self, key: str):
        self._map_label_mode = key
        for k, b in self._map_label_btns.items(): b.setChecked(k == key)

    def _open_map_preview(self):
        """Открывает карту для просмотра (без рисования)."""
        settings = self._collect_map_settings()
        dlg = MapPreviewDialog(settings=settings, editable=False, parent=self)
        dlg.exec()

    def _open_map_editor(self):
        """Открывает карту для рисования территорий."""
        settings = self._collect_map_settings()
        dlg = MapPreviewDialog(settings=settings, editable=True, parent=self)
        if dlg.exec():
            self._territories = dlg.get_territories()
            self._refresh_territory_list()

    def _collect_map_settings(self) -> dict:
        return {
            'markers':     list(self._manual_markers),
            'territories': list(self._territories),
            'view_mode':   getattr(self, '_map_view_mode', 'point'),
            'area_radius': getattr(self, '_area_radius_spin', None) and self._area_radius_spin.value() or 1000,
            'label_mode':  getattr(self, '_map_label_mode', 'name'),
            'icon_style':  getattr(self, '_map_icon_key', 'pin'),
        }

    def _refresh_territory_list(self):
        self._territory_list.clear()
        for i, poly in enumerate(self._territories):
            pts = len(poly)
            self._territory_list.addItem(QListWidgetItem(f"🟩 Территория {i+1} ({pts} точек)"))

    def _clear_territories(self):
        self._territories = []
        self._refresh_territory_list()

    def _on_map_addr_changed(self):
        pass  # оставлено для совместимости

    def _geocode_address(self):
        """Геокодирует введённый адрес и добавляет маркер в список."""
        city   = self._map_city_input.text().strip()   if hasattr(self, '_map_city_input')   else ''
        street = self._map_street_input.text().strip() if hasattr(self, '_map_street_input') else ''
        house  = self._map_house_input.text().strip()  if hasattr(self, '_map_house_input')  else ''

        parts = [p for p in [house, street, city, 'Нижегородская область', 'Россия'] if p]
        if not city:
            self._geo_result_lbl.setText("⚠ Введите хотя бы населённый пункт")
            self._geo_result_lbl.setStyleSheet(f"font-size:10px;color:{ACCENT_RED};background:transparent;")
            return

        self._geo_result_lbl.setText("⏳ Поиск…")
        self._geo_result_lbl.setStyleSheet(f"font-size:10px;color:{TEXT_MUT};background:transparent;")

        try:
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            import urllib.request, json as _json, urllib.parse
            query  = ', '.join(parts)
            params = urllib.parse.urlencode({
                'q': query, 'format': 'json', 'limit': '1',
                'accept-language': 'ru', 'countrycodes': 'ru'
            })
            url = f"https://nominatim.openstreetmap.org/search?{params}"
            req = urllib.request.Request(url, headers={'User-Agent': 'EcologyBI/1.0'})
            with urllib.request.urlopen(req, timeout=7) as resp:
                data = _json.loads(resp.read().decode())

            if data:
                self._geo_lat = float(data[0]['lat'])
                self._geo_lon = float(data[0]['lon'])
                name = ', '.join(p for p in [house, street, city] if p)
                # Добавляем маркер в список
                marker = {
                    'name':       name,
                    'lat':        self._geo_lat,
                    'lon':        self._geo_lon,
                    'city':       city,
                    'street':     street,
                    'house':      house,
                    'label_mode': getattr(self, '_map_label_mode', 'name'),
                    'icon':       getattr(self, '_map_icon_key', 'pin'),
                    'color':      '#4caf50',
                }
                self._manual_markers.append(marker)
                self._refresh_marker_list()
                self._geo_result_lbl.setText(f"✅ Добавлен маркер: {name}")
                self._geo_result_lbl.setStyleSheet(f"font-size:10px;color:{ACCENT};background:transparent;")
                # Очищаем поля
                self._map_city_input.clear()
                self._map_street_input.clear()
                self._map_house_input.clear()
            else:
                self._geo_result_lbl.setText("❌ Адрес не найден")
                self._geo_result_lbl.setStyleSheet(f"font-size:10px;color:{ACCENT_RED};background:transparent;")
        except Exception:
            self._geo_result_lbl.setText("⚠ Ошибка соединения")
            self._geo_result_lbl.setStyleSheet(f"font-size:10px;color:{TEXT_MUT};background:transparent;")

        self._update_preview()

    # ─── Дополнительная панель ──────────────────────────────────────────────

    def _build_advanced_panel(self) -> QWidget:
        panel = QFrame()
        panel.setStyleSheet(
            f"QFrame {{ background:{BG_PANEL}; border:1px solid {BORDER}; border-radius:6px; }}"
        )
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(10)

        # ── Цвет ──────────────────────────────────────────────────────────────
        color_row = QHBoxLayout()
        color_lbl = QLabel("Цвет:")
        color_lbl.setStyleSheet(f"font-size:12px; color:{TEXT_SEC}; background:transparent; border:none;")
        color_row.addWidget(color_lbl)
        self._color_preview = _color_swatch(self._kpi_color)
        color_row.addWidget(self._color_preview)
        color_btn = _small_btn("Выбрать"); color_btn.clicked.connect(self._pick_color)
        color_row.addWidget(color_btn)
        color_row.addStretch()
        lay.addLayout(color_row)

        # ── Чекбоксы (Chart) ──────────────────────────────────────────────────
        self._chart_options_row = QWidget()
        co_lay = QHBoxLayout(self._chart_options_row)
        co_lay.setContentsMargins(0, 0, 0, 0); co_lay.setSpacing(16)
        self._show_grid_cb   = QCheckBox("Сетка"); self._show_grid_cb.setChecked(True)
        self._show_values_cb = QCheckBox("Подписи значений")
        co_lay.addWidget(self._show_grid_cb); co_lay.addWidget(self._show_values_cb)
        co_lay.addStretch()
        lay.addWidget(self._chart_options_row)

        # ── Максимум категорий ────────────────────────────────────────────────
        self._max_items_row = QWidget()
        mi_lay = QHBoxLayout(self._max_items_row)
        mi_lay.setContentsMargins(0, 0, 0, 0); mi_lay.setSpacing(8)
        mi_lbl = QLabel("Показывать не более:")
        mi_lbl.setStyleSheet(f"font-size:12px; color:{TEXT_SEC}; background:transparent; border:none;")
        mi_lay.addWidget(mi_lbl)
        self._max_items_spin = QSpinBox()
        self._max_items_spin.setRange(3, 100); self._max_items_spin.setValue(15)
        self._max_items_spin.setFixedWidth(80); self._max_items_spin.setSuffix(" кат.")
        mi_lay.addWidget(self._max_items_spin); mi_lay.addStretch()
        lay.addWidget(self._max_items_row)

        # ── Размер шрифта (KPI) ───────────────────────────────────────────────
        self._font_size_row = QWidget()
        fs_lay = QHBoxLayout(self._font_size_row)
        fs_lay.setContentsMargins(0, 0, 0, 0); fs_lay.setSpacing(8)
        fs_lbl = QLabel("Размер числа:")
        fs_lbl.setStyleSheet(f"font-size:12px; color:{TEXT_SEC}; background:transparent; border:none;")
        fs_lay.addWidget(fs_lbl)
        self._font_size = QSpinBox()
        self._font_size.setRange(16, 72); self._font_size.setValue(36)
        self._font_size.setFixedWidth(80)
        self._font_size.valueChanged.connect(self._update_preview)
        fs_lay.addWidget(self._font_size); fs_lay.addStretch()
        lay.addWidget(self._font_size_row)

        # ── Лимит строк (Table) ───────────────────────────────────────────────
        self._limit_row = QWidget()
        lm_lay = QHBoxLayout(self._limit_row)
        lm_lay.setContentsMargins(0, 0, 0, 0); lm_lay.setSpacing(8)
        lm_lbl = QLabel("Максимум строк:")
        lm_lbl.setStyleSheet(f"font-size:12px; color:{TEXT_SEC}; background:transparent; border:none;")
        lm_lay.addWidget(lm_lbl)
        self._limit_spin = QSpinBox()
        self._limit_spin.setRange(5, 500); self._limit_spin.setValue(50)
        self._limit_spin.setFixedWidth(80)
        lm_lay.addWidget(self._limit_spin); lm_lay.addStretch()
        lay.addWidget(self._limit_row)

        return panel

    # ── Ручные маркеры ────────────────────────────────────────────────────────

    _STATUS_ICONS = {'норма': '🟢', 'превышение': '🟡', 'критично': '🔴'}
    _ICON_CHARS   = {'pin':'●','circle':'○','pulse':'◎','star':'★','flag':'⚑','dot':'·'}

    def _refresh_marker_list(self):
        self._marker_list.clear()
        for m in self._manual_markers:
            status_icon = self._STATUS_ICONS.get(m.get('status', 'норма'), '⚪')
            icon_char   = self._ICON_CHARS.get(m.get('icon', 'pin'), '●')
            lmode_short = {'name':'имя','address':'адрес','coords':'коорд.','none':'—'
                           }.get(m.get('label_mode','name'), '')
            val_str = f"  ·  {m['value']} {m.get('unit','')}".rstrip() if m.get('value') else ''
            label = f"{status_icon} {icon_char}  {m.get('name','—')}  [{lmode_short}]{val_str}"
            self._marker_list.addItem(QListWidgetItem(label))

    def _add_manual_marker(self):
        dlg = MarkerEditorDialog(parent=self)
        if dlg.exec():
            self._manual_markers.append(dlg.get_marker_data())
            self._refresh_marker_list()

    def _edit_manual_marker(self):
        idx = self._marker_list.currentRow()
        if idx < 0 or idx >= len(self._manual_markers): return
        dlg = MarkerEditorDialog(marker=self._manual_markers[idx], parent=self)
        if dlg.exec():
            self._manual_markers[idx] = dlg.get_marker_data()
            self._refresh_marker_list()

    def _remove_manual_marker(self):
        idx = self._marker_list.currentRow()
        if idx < 0 or idx >= len(self._manual_markers): return
        self._manual_markers.pop(idx)
        self._refresh_marker_list()

    # ─── Выбор типа ─────────────────────────────────────────────────────────

    def _select_type(self, key: str):
        self._current_type = key

        for k, card in self._type_cards.items():
            if isinstance(card, TypeCard):
                card.set_selected(k == key)
            else:
                card.setChecked(k == key)

        is_kpi      = key == 'kpi'
        is_chart    = key == 'chart'
        is_table    = key == 'table'
        is_text     = key == 'text'
        is_image    = key == 'image'
        is_map      = key == 'map'
        is_stub     = key in ('gauge', 'progress', 'pivot')
        has_source  = key in ('kpi', 'chart', 'table')

        self._source_combo.blockSignals(True)
        self._source_combo.clear()
        if is_kpi:
            self._source_label.setText("Показатель:")
            for val, label in KPI_CHOICES:
                self._source_combo.addItem(label, val)
        elif is_chart:
            self._source_label.setText("Данные для графика:")
            for val, label in CHART_CHOICES:
                self._source_combo.addItem(label, val)
        elif is_table:
            self._source_label.setText("Данные для таблицы:")
            for val, label in TABLE_CHOICES:
                self._source_combo.addItem(label, val)
        self._source_combo.blockSignals(False)

        self._source_label.setVisible(has_source)
        self._source_combo.setVisible(has_source)

        self._chart_style_row.setVisible(is_chart)
        self._kpi_mode_row.setVisible(is_kpi)
        self._text_settings_w.setVisible(is_text)
        self._image_settings_w.setVisible(is_image)
        self._map_settings_w.setVisible(is_map)
        if hasattr(self, '_stub_settings_w'):
            self._stub_settings_w.setVisible(is_stub)

        if is_kpi:
            self._kpi_dataset_btn.setEnabled(bool(self._datasets))
            self._set_kpi_mode('manual')
        else:
            self._manual_label.hide(); self._manual_value.hide()
            self._kpi_unit_label.hide(); self._kpi_unit_edit.hide()

        self._chart_options_row.setVisible(is_chart)
        self._max_items_row.setVisible(is_chart or is_table)
        self._font_size_row.setVisible(is_kpi)
        self._limit_row.setVisible(is_table)

        # Подпись скрываем для текста/изображения (у них свои поля)
        self._title_lbl_widget.setVisible(not is_text and not is_image)
        self._title_edit.setVisible(not is_text and not is_image)

        if is_stub:
            _stub_hints = {
                'gauge':    'Значение / источник для датчика:',
                'progress': 'Значение / источник для прогресс-бара:',
                'pivot':    'Значение / источник для сводной таблицы:',
            }
            if hasattr(self, '_stub_label'):
                self._stub_label.setText(_stub_hints.get(key, 'Значение:'))

        self._update_preview()

    def _select_chart_style(self, key: str):
        self._chart_style_key = key
        for k, btn in self._chart_style_btns.items():
            btn.setChecked(k == key)
        self._update_preview()

    def _set_kpi_mode(self, mode: str):
        self._kpi_manual_btn.setChecked(mode == 'manual')
        self._kpi_dataset_btn.setChecked(mode == 'dataset')
        is_manual = (mode == 'manual')
        # Eco source_combo скрыт для KPI — вместо него используем _kpi_col_row
        self._source_label.setVisible(False)
        self._source_combo.setVisible(False)
        self._manual_label.setVisible(is_manual)
        self._manual_value.setVisible(is_manual)
        self._kpi_unit_label.setVisible(is_manual)
        self._kpi_unit_edit.setVisible(is_manual)
        if hasattr(self, '_kpi_col_row'):
            self._kpi_col_row.setVisible(not is_manual)
            if not is_manual:
                self._populate_kpi_columns()
        self._update_preview()

    def _populate_kpi_columns(self):
        """Заполняет _kpi_column_combo столбцами из выбранного датасета."""
        if not hasattr(self, '_kpi_column_combo'):
            return
        self._kpi_column_combo.blockSignals(True)
        prev = self._kpi_column_combo.currentData()
        self._kpi_column_combo.clear()
        dataset_name = self._dataset_combo.currentData() if hasattr(self, '_dataset_combo') else ''
        if dataset_name and dataset_name in self._datasets:
            df = self._datasets[dataset_name]
            if hasattr(df, 'columns'):
                for col in df.columns:
                    self._kpi_column_combo.addItem(col, col)
        if self._kpi_column_combo.count() == 0:
            self._kpi_column_combo.addItem("— нет столбцов —", "")
        # Восстанавливаем предыдущий выбор если возможно
        if prev:
            idx = self._kpi_column_combo.findData(prev)
            if idx >= 0:
                self._kpi_column_combo.setCurrentIndex(idx)
        self._kpi_column_combo.blockSignals(False)

    def _on_dataset_changed(self):
        """При смене датасета обновляем список столбцов в KPI-режиме датасета."""
        if (self._current_type == 'kpi'
                and hasattr(self, '_kpi_dataset_btn')
                and self._kpi_dataset_btn.isChecked()):
            self._populate_kpi_columns()
        self._update_preview()

    def _set_text_align(self, key: str):
        self._text_align_key = key
        for k, btn in self._text_align_btns.items():
            btn.setChecked(k == key)
        self._update_preview()

    def _toggle_advanced(self):
        self._advanced_visible = not self._advanced_visible
        self._adv_panel.setVisible(self._advanced_visible)
        arrow = '▾' if self._advanced_visible else '▸'
        self._adv_toggle.setText(f"{arrow}  Дополнительные настройки")

    # ─── Цвета ──────────────────────────────────────────────────────────────

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self._kpi_color), self)
        if c.isValid():
            self._kpi_color = self._chart_color = c.name()
            self._color_preview.setStyleSheet(
                f"background:{c.name()}; border-radius:4px; border:1px solid {BORDER_LT};"
            )
            self._update_preview()

    def _pick_text_color(self):
        c = QColorDialog.getColor(QColor(self._text_color), self)
        if c.isValid():
            self._text_color = c.name()
            self._text_color_preview.setStyleSheet(
                f"background:{c.name()}; border-radius:3px; border:1px solid {BORDER_LT};"
            )
            self._update_preview()

    def _pick_text_bg(self):
        start = self._text_bg_color if self._text_bg_color != 'transparent' else '#1C2E1C'
        c = QColorDialog.getColor(QColor(start), self)
        if c.isValid():
            self._text_bg_color = c.name()
            self._text_bg_preview.setStyleSheet(
                f"background:{c.name()}; border-radius:3px; border:1px solid {BORDER_LT};"
            )
            self._update_preview()

    def _on_opacity_changed(self, val: int):
        self._opacity_value_lbl.setText(f"{val}%")
        self._update_preview()

    def _browse_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение", "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.svg *.webp);;Все файлы (*)"
        )
        if path:
            self._image_path = path
            self._image_path_edit.setText(os.path.basename(path))
            self._update_preview()

    # ─── Превью ─────────────────────────────────────────────────────────────

    def _update_preview(self):
        t = self._current_type
        if   t == 'kpi':      self._preview_kpi()
        elif t == 'chart':    self._preview_chart()
        elif t == 'table':    self._preview_table()
        elif t == 'text':     self._preview_text()
        elif t == 'image':    self._preview_image()
        elif t == 'map':      self._preview_map()
        elif t in ('gauge', 'progress', 'pivot'):
            self._preview_stub(t)

    def _preview_kpi(self):
        adv_open  = hasattr(self, '_adv_panel') and self._adv_panel.isVisible()
        size      = self._font_size.value() if (adv_open and hasattr(self, '_font_size')) else 36
        color     = self._kpi_color
        title_txt = self._title_edit.text() if hasattr(self, '_title_edit') else ''
        is_manual = hasattr(self, '_kpi_manual_btn') and self._kpi_manual_btn.isChecked()

        if is_manual:
            value = (self._manual_value.text() if hasattr(self, '_manual_value') else '') or '—'
            unit  = self._kpi_unit_edit.text() if hasattr(self, '_kpi_unit_edit') else ''
            title = title_txt or 'Значение'
        else:
            col_name     = (self._kpi_column_combo.currentData()
                            if hasattr(self, '_kpi_column_combo') else '') or ''
            agg_key      = (self._kpi_agg_combo.currentData()
                            if hasattr(self, '_kpi_agg_combo') else 'sum') or 'sum'
            agg_label    = (self._kpi_agg_combo.currentText()
                            if hasattr(self, '_kpi_agg_combo') else 'Сумма')
            dataset_name = (self._dataset_combo.currentData()
                            if hasattr(self, '_dataset_combo') else '') or ''
            value = '···'
            if col_name and dataset_name and dataset_name in self._datasets:
                try:
                    import pandas as _pd
                    df  = self._datasets[dataset_name]
                    col = df[col_name].dropna()
                    if   agg_key == 'sum':   val = col.sum()
                    elif agg_key == 'avg':   val = round(float(col.mean()), 2)
                    elif agg_key == 'count': val = len(col)
                    elif agg_key == 'max':   val = col.max()
                    elif agg_key == 'min':   val = col.min()
                    elif agg_key == 'first': val = col.iloc[0] if len(col) > 0 else '—'
                    else:                    val = col.sum()
                    if isinstance(val, float) and val == int(val):
                        val = int(val)
                    value = str(val)
                except Exception:
                    value = '—'
            unit  = ''
            title = title_txt or f"{agg_label}: {col_name or 'столбец'}"

        unit_html = (
            f"<span style='font-size:{max(11,size//3)}px;color:{color}99;margin-left:5px;'>{unit}</span>"
        ) if unit else ''
        self._preview.setText(
            f"<div style='text-align:center;padding:14px 10px;background:{BG_CARD};'>"
            f"<div style='font-size:{size}px;font-weight:bold;color:{color};'>{value}{unit_html}</div>"
            f"<div style='font-size:11px;color:{TEXT_MUT};margin-top:6px;'>{title}</div>"
            f"</div>"
        )

    def _preview_chart(self):
        title = (self._title_edit.text() if hasattr(self, '_title_edit') else '') or \
                (self._source_combo.currentText() if hasattr(self, '_source_combo') else '')
        color = self._chart_color
        style = self._chart_style_key
        vals   = [42, 78, 55, 91, 38, 67, 84]
        labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        mx = max(vals)
        pw = max(320, self._preview.width())
        ph = 148; W = pw; H = ph - 22

        if style == 'bar':
            step = W / (len(vals)+1); bw = max(16, step-10); shapes = ''
            for i, v in enumerate(vals):
                bh = int(v/mx*(H-18)); x = int(step*(i+1)-bw/2); y = H-4-bh
                op = '1' if i%2==0 else '0.73'
                shapes += (f"<rect x='{x}' y='{y}' width='{int(bw)}' height='{bh}' "
                           f"fill='{color}' fill-opacity='{op}' rx='2'/>"
                           f"<text x='{x+int(bw)//2}' y='{H+8}' text-anchor='middle' "
                           f"font-size='7' fill='{TEXT_MUT}'>{labels[i]}</text>")
        elif style == 'scatter':
            shapes = ''
            for i, v in enumerate(vals):
                x = int(20+i*38+10); y = int(H-8-v/mx*(H-20))
                shapes += (f"<circle cx='{x}' cy='{y}' r='5' fill='{color}' fill-opacity='0.8'/>"
                           f"<circle cx='{x}' cy='{y}' r='2' fill='{color}'/>")
        elif style == 'radar':
            n=6; cx=W//2; cy=H//2; r=min(W,H)//2-10; shapes=''
            for ring in [0.33,0.66,1.0]:
                pts=' '.join(f"{cx+r*ring*math.cos(2*math.pi*i/n-math.pi/2):.1f},"
                             f"{cy+r*ring*math.sin(2*math.pi*i/n-math.pi/2):.1f}" for i in range(n))
                shapes+=f"<polygon points='{pts}' fill='none' stroke='{BORDER}' stroke-width='1'/>"
            dr=[0.85,0.6,0.9,0.5,0.75,0.65]
            dp=' '.join(f"{cx+r*dr[i]*math.cos(2*math.pi*i/n-math.pi/2):.1f},"
                        f"{cy+r*dr[i]*math.sin(2*math.pi*i/n-math.pi/2):.1f}" for i in range(n))
            shapes+=f"<polygon points='{dp}' fill='{color}' fill-opacity='0.2' stroke='{color}' stroke-width='2'/>"
        elif style == 'heatmap':
            cols_h,rows_h=7,3; cw=(W-20)//cols_h; rh=(H-16)//rows_h
            hd=[0.9,0.4,0.7,0.2,0.8,0.5,0.6,0.3,0.9,0.5,0.7,0.4,0.8,0.2,0.6,0.3,0.8,0.6,0.3,0.9,0.5]
            shapes=''
            for ri in range(rows_h):
                for ci in range(cols_h):
                    v=hd[ri*cols_h+ci]; op=round(v*0.78+0.22,2); x=10+ci*cw; y=8+ri*rh
                    shapes+=f"<rect x='{x}' y='{y}' width='{cw-2}' height='{rh-2}' fill='{color}' fill-opacity='{op}' rx='2'/>"
        elif style == 'treemap':
            shapes=(f"<rect x='4' y='4' width='160' height='{H-8}' fill='{color}' fill-opacity='0.93' rx='3'/>"
                    f"<text x='84' y='{H//2+4}' text-anchor='middle' font-size='9' fill='{TEXT_PRI}'>52%</text>"
                    f"<rect x='168' y='4' width='128' height='{H//2-4}' fill='{color}' fill-opacity='0.6' rx='3'/>"
                    f"<text x='232' y='{H//4+4}' text-anchor='middle' font-size='8' fill='{TEXT_PRI}'>30%</text>"
                    f"<rect x='168' y='{H//2+2}' width='128' height='{H//2-6}' fill='{color}' fill-opacity='0.4' rx='3'/>"
                    f"<text x='232' y='{H*3//4+4}' text-anchor='middle' font-size='8' fill='{TEXT_PRI}'>18%</text>")
        else:
            sx=(W-30)/(len(vals)-1)
            pts=' '.join(f"{int(15+i*sx)},{int(H-8-v/mx*(H-20))}" for i,v in enumerate(vals))
            lx=int(15+(len(vals)-1)*sx)
            if style=='area':
                shapes=(f"<polygon points='{pts} {lx},{H-8} 15,{H-8}' fill='{color}' fill-opacity='0.13'/>"
                        f"<polyline points='{pts}' fill='none' stroke='{color}' stroke-width='2' stroke-linejoin='round'/>")
            else:
                shapes=f"<polyline points='{pts}' fill='none' stroke='{color}' stroke-width='2.5' stroke-linejoin='round'/>"
                for i,v in enumerate(vals):
                    px=int(15+i*sx); py=int(H-8-v/mx*(H-20))
                    shapes+=f"<circle cx='{px}' cy='{py}' r='3' fill='{color}'/>"

        axes=(f"<line x1='12' y1='4' x2='12' y2='{H-4}' stroke='{BORDER}' stroke-width='1'/>"
              f"<line x1='12' y1='{H-4}' x2='{W-4}' y2='{H-4}' stroke='{BORDER}' stroke-width='1'/>") \
             if style not in ('radar','heatmap','treemap') else ''

        sl = next((l for k,l in CHART_STYLES if k==style), style)
        tl = f"{title}  ▪ {sl}" if title else sl
        svg=(f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{ph}' viewBox='0 0 {W} {ph}'>"
             f"<rect width='{W}' height='{ph}' fill='{BG_CARD}'/>"
             f"<text x='10' y='14' font-size='11' font-weight='bold' fill='{TEXT_SEC}'>{tl}</text>"
             f"<g transform='translate(0,20)'>{axes}{shapes}</g></svg>")
        renderer = QSvgRenderer(QByteArray(svg.encode('utf-8')))
        if renderer.isValid():
            pix = QPixmap(W, ph); pix.fill(QColor(BG_CARD))
            painter = QPainter(pix)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            renderer.render(painter); painter.end()
            self._preview.setPixmap(pix)
        else:
            self._preview.setText(f"<div style='text-align:center;padding:20px;color:{TEXT_MUT};'>📊 {sl}</div>")

    def _preview_table(self):
        title = (self._title_edit.text() if hasattr(self,'_title_edit') else '') or \
                (self._source_combo.currentText() if hasattr(self,'_source_combo') else '')
        rows  = [('Мусор и свалки','48','42','88%'),('Водоёмы','31','25','81%'),
                 ('Выбросы','27','19','70%'),('Почвы','14','12','86%')]
        rh = ''.join(
            f"<tr style='{'background:'+BG_PANEL+';' if i%2==0 else ''}'>"
            f"<td style='padding:4px 8px;color:{TEXT_PRI};'>{c}</td>"
            f"<td style='padding:4px 8px;color:{TEXT_SEC};text-align:center;'>{t}</td>"
            f"<td style='padding:4px 8px;color:{ACCENT};text-align:center;'>{d}</td>"
            f"<td style='padding:4px 8px;color:{TEXT_MUT};text-align:center;'>{p}</td></tr>"
            for i,(c,t,d,p) in enumerate(rows)
        )
        self._preview.setText(
            f"<div style='padding:8px 10px;background:{BG_CARD};'>"
            f"<div style='font-weight:bold;font-size:11px;color:{TEXT_SEC};margin-bottom:5px;'>{title}</div>"
            f"<table width='100%' style='font-size:10px;border-collapse:collapse;'>"
            f"<tr style='background:{BG_DARK};'>"
            f"<td style='padding:4px 8px;color:{TEXT_MUT};font-weight:bold;'>Категория</td>"
            f"<td style='padding:4px 8px;color:{TEXT_MUT};font-weight:bold;text-align:center;'>Всего</td>"
            f"<td style='padding:4px 8px;color:{TEXT_MUT};font-weight:bold;text-align:center;'>Выполнено</td>"
            f"<td style='padding:4px 8px;color:{TEXT_MUT};font-weight:bold;text-align:center;'>%</td></tr>"
            f"{rh}</table></div>"
        )

    def _preview_text(self):
        text   = self._text_content.toPlainText() if hasattr(self,'_text_content') else ''
        size   = self._text_font_size.value() if hasattr(self,'_text_font_size') else 14
        bold   = 'bold'   if (hasattr(self,'_text_bold_btn')   and self._text_bold_btn.isChecked())   else 'normal'
        italic = 'italic' if (hasattr(self,'_text_italic_btn') and self._text_italic_btn.isChecked()) else 'normal'
        align  = self._text_align_key if hasattr(self,'_text_align_key') else 'left'
        color  = self._text_color
        bg     = self._text_bg_color if self._text_bg_color != 'transparent' else BG_CARD
        disp   = text or '<span style="opacity:0.4">Текст будет здесь…</span>'
        self._preview.setText(
            f"<div style='padding:16px 18px;background:{bg};height:100%;'>"
            f"<div style='font-size:{size}px;font-weight:{bold};font-style:{italic};"
            f"color:{color};text-align:{align};word-wrap:break-word;'>{disp}</div></div>"
        )

    def _preview_image(self):
        path    = self._image_path
        opacity = self._image_opacity.value() if hasattr(self,'_image_opacity') else 100
        fit     = self._image_fit_combo.currentData() if hasattr(self,'_image_fit_combo') else 'contain'
        fl = {'contain':'По размеру','cover':'Заполнить','fill':'Растянуть','center':'По центру'}
        if path and os.path.isfile(path):
            self._preview.setText(
                f"<div style='text-align:center;padding:20px;background:{BG_CARD};'>"
                f"<div style='font-size:28px;'>🖼</div>"
                f"<div style='font-size:12px;color:{TEXT_PRI};margin-top:6px;font-weight:bold;'>{os.path.basename(path)}</div>"
                f"<div style='font-size:10px;color:{TEXT_MUT};margin-top:4px;'>Непрозрачность: {opacity}%  ·  {fl.get(fit,fit)}</div>"
                f"</div>"
            )
        else:
            self._preview.setText(
                f"<div style='text-align:center;padding:30px 20px;'>"
                f"<div style='font-size:36px;'>🖼</div>"
                f"<div style='color:{TEXT_MUT};font-size:11px;margin-top:8px;'>Выберите файл изображения</div>"
                f"</div>"
            )

    def _preview_map(self):
        markers    = getattr(self, '_manual_markers', [])
        n          = len(markers)
        view_mode  = getattr(self, '_map_view_mode', 'point')
        icon_key   = getattr(self, '_map_icon_key', 'pin')
        label_mode = getattr(self, '_map_label_mode', 'name')
        territories = getattr(self, '_territories', [])

        area_radius = getattr(self, '_area_radius_spin', None)
        radius_val  = area_radius.value() if area_radius else 1000
        vm_labels = {
            'point':      'По точке',
            'settlement': 'Нас. пункт',
            'district':   'Район',
            'region':     'Область',
            'radius':     f'Радиус {radius_val} м',
            'polygon':    'По площади',
        }
        ik_chars  = {'pin':'●','circle':'○','pulse':'◎','star':'★','flag':'⚑','dot':'·'}
        lm_labels = {'name':'Название','address':'Адрес','coords':'Координаты','none':'Без подписи'}

        marker_names = ', '.join(m.get('name','') for m in markers[:3]) if markers else ''
        if n > 3: marker_names += f' +{n-3}'

        ter_info = (f"<div style='font-size:10px;color:{ACCENT};margin-top:3px;'>"
                    f"🟩 {len(territories)} территори{'я' if len(territories)==1 else 'и'}</div>"
                    ) if territories else ''

        self._preview.setText(
            f"<div style='text-align:center;padding:14px;background:{BG_CARD};'>"
            f"<div style='font-size:30px;'>🗺</div>"
            f"<div style='color:{TEXT_SEC};font-size:12px;margin-top:6px;font-weight:bold;'>"
            f"Карта  ·  {vm_labels.get(view_mode, view_mode)}</div>"
            f"<div style='color:{ACCENT};font-size:11px;margin-top:4px;'>"
            f"{ik_chars.get(icon_key,'●')} {n} маркер{'ов' if n!=1 else ''}  ·  {lm_labels.get(label_mode,'')}</div>"
            + (f"<div style='color:{TEXT_MUT};font-size:10px;margin-top:3px;'>{marker_names}</div>" if marker_names else "")
            + ter_info +
            f"<div style='color:{TEXT_MUT};font-size:10px;margin-top:6px;'>"
            f"Нажмите «Просмотр карты» для предпросмотра</div>"
            f"</div>"
        )

    def _preview_stub(self, stub_type: str):
        _svg_map = {'gauge': _SVG_GAUGE, 'progress': _SVG_PROGRESS, 'pivot': _SVG_PIVOT}
        _name_map = {'gauge': 'Датчик', 'progress': 'Прогресс', 'pivot': 'Сводная таблица'}
        svg = _svg_map.get(stub_type, '')
        pw = max(320, self._preview.width())
        ph = 148
        if svg:
            renderer = QSvgRenderer(QByteArray(svg.strip().encode('utf-8')))
            if renderer.isValid():
                pix = QPixmap(pw, ph)
                pix.fill(QColor(BG_CARD))
                painter = QPainter(pix)
                painter.setRenderHint(QPainter.Antialiasing)
                # рендерим SVG в центре превью
                aspect = 64 / 52
                h = int(ph * 0.7); w = int(h * aspect)
                x = (pw - w) // 2; y = (ph - h) // 2
                from PySide6.QtCore import QRectF
                renderer.render(painter, QRectF(x, y, w, h))
                painter.end()
                self._preview.setPixmap(pix)
                return
        name = _name_map.get(stub_type, stub_type)
        self._preview.setText(
            f"<div style='text-align:center;padding:30px;color:{TEXT_MUT};'>"
            f"<div style='font-size:13px;font-weight:bold;color:{TEXT_SEC};'>{name}</div>"
            f"</div>"
        )

    # ─── Создание виджета ──────────────────────────────────────────────────

    def _on_add(self):
        t            = self._current_type
        title        = self._title_edit.text().strip() if hasattr(self,'_title_edit') else ''
        color        = self._kpi_color
        dataset_name = self._dataset_combo.currentData() if hasattr(self,'_dataset_combo') else ''

        if t == 'kpi':
            is_manual = self._kpi_manual_btn.isChecked()
            if is_manual:
                settings = {
                    'metric':       'manual',
                    'title':        title or self._manual_value.text() or 'Значение',
                    'value':        self._manual_value.text(),
                    'unit':         self._kpi_unit_edit.text(),
                    'color':        color,
                    'font_size':    self._font_size.value(),
                    'dataset_name': dataset_name,
                }
            else:
                col_name  = (self._kpi_column_combo.currentData()
                             if hasattr(self, '_kpi_column_combo') else '') or ''
                agg       = (self._kpi_agg_combo.currentData()
                             if hasattr(self, '_kpi_agg_combo') else 'sum') or 'sum'
                agg_label = (self._kpi_agg_combo.currentText()
                             if hasattr(self, '_kpi_agg_combo') else 'Сумма')
                settings = {
                    'metric':       'column',
                    'column_name':  col_name,
                    'aggregation':  agg,
                    'title':        title or f"{agg_label}: {col_name or 'столбец'}",
                    'value':        '',
                    'unit':         '',
                    'color':        color,
                    'font_size':    self._font_size.value(),
                    'dataset_name': dataset_name,
                }
        elif t == 'chart':
            src_key = self._source_combo.currentData() or 'none'
            src_lbl = self._source_combo.currentText()
            settings = {
                'data_source':  src_key,
                'chart_style':  self._chart_style_key,
                'title':        title or src_lbl,
                'color':        self._chart_color,
                'show_grid':    self._show_grid_cb.isChecked(),
                'show_values':  self._show_values_cb.isChecked(),
                'max_items':    self._max_items_spin.value(),
                'dataset_name': dataset_name,
            }
        elif t == 'table':
            src_key = self._source_combo.currentData() or 'none'
            src_lbl = self._source_combo.currentText()
            settings = {
                'data_source':  src_key,
                'title':        title or src_lbl,
                'limit':        self._limit_spin.value(),
                'max_items':    self._max_items_spin.value(),
                'dataset_name': dataset_name,
            }
        elif t == 'text':
            settings = {
                'title':    title or 'Текст',
                'content':  self._text_content.toPlainText(),
                'font_size':self._text_font_size.value(),
                'bold':     self._text_bold_btn.isChecked(),
                'italic':   self._text_italic_btn.isChecked(),
                'align':    self._text_align_key,
                'color':    self._text_color,
                'bg_color': self._text_bg_color,
            }
        elif t == 'image':
            settings = {
                'title':   title or 'Изображение',
                'path':    self._image_path,
                'opacity': self._image_opacity.value(),
                'fit':     self._image_fit_combo.currentData() or 'contain',
            }
        elif t == 'map':
            settings = {
                'title':       title or 'Карта',
                'markers':     list(self._manual_markers),
                'territories': list(self._territories),
                'view_mode':   getattr(self, '_map_view_mode', 'point'),
                'area_radius': getattr(self, '_area_radius_spin', None) and self._area_radius_spin.value() or 1000,
                'label_mode':  getattr(self, '_map_label_mode', 'name'),
                'icon_style':  getattr(self, '_map_icon_key', 'pin'),
                'dataset_name': dataset_name,
            }
        elif t in ('gauge', 'progress', 'pivot'):
            _default_titles = {'gauge': 'Датчик', 'progress': 'Прогресс', 'pivot': 'Сводная'}
            val = (self._stub_value_edit.text().strip()
                   if hasattr(self, '_stub_value_edit') else '')
            settings = {
                'title':        title or _default_titles.get(t, t),
                'value':        val,
                'color':        color,
                'dataset_name': dataset_name,
            }
        else:
            settings = {}

        self.widget_created.emit(t, settings)
        self.accept()

    # ─── Предзаполнение (редактирование) ──────────────────────────────────

    def load_settings(self, widget_type: str, settings: dict):
        self._select_type(widget_type)

        if widget_type == 'kpi':
            metric = settings.get('metric', 'manual')
            if metric == 'column':
                self._set_kpi_mode('dataset')
                # _populate_kpi_columns вызывается внутри _set_kpi_mode,
                # но датасет ещё не выбран — сначала выберем его
                ds_idx = self._dataset_combo.findData(settings.get('dataset_name', ''))
                if ds_idx >= 0:
                    self._dataset_combo.blockSignals(True)
                    self._dataset_combo.setCurrentIndex(ds_idx)
                    self._dataset_combo.blockSignals(False)
                self._populate_kpi_columns()
                if hasattr(self, '_kpi_column_combo'):
                    idx = self._kpi_column_combo.findData(settings.get('column_name', ''))
                    if idx >= 0:
                        self._kpi_column_combo.setCurrentIndex(idx)
                if hasattr(self, '_kpi_agg_combo'):
                    idx = self._kpi_agg_combo.findData(settings.get('aggregation', 'sum'))
                    if idx >= 0:
                        self._kpi_agg_combo.setCurrentIndex(idx)
            elif metric == 'manual':
                self._set_kpi_mode('manual')
                self._manual_value.setText(settings.get('value', ''))
                self._kpi_unit_edit.setText(settings.get('unit', ''))
            else:
                # Старые eco-метрики — показываем как ручное значение
                self._set_kpi_mode('manual')
                self._manual_value.setText(settings.get('value', ''))
                self._kpi_unit_edit.setText(settings.get('unit', ''))
            self._kpi_color = settings.get('color', ACCENT_DARK)
            self._font_size.setValue(settings.get('font_size', 36))
        elif widget_type == 'chart':
            self._set_combo(self._source_combo, settings.get('data_source', 'none'))
            self._chart_color = settings.get('color', ACCENT)
            self._select_chart_style(settings.get('chart_style', 'bar'))
            self._show_grid_cb.setChecked(settings.get('show_grid', True))
            self._show_values_cb.setChecked(settings.get('show_values', False))
            self._max_items_spin.setValue(settings.get('max_items', 15))
        elif widget_type == 'table':
            self._set_combo(self._source_combo, settings.get('data_source', 'none'))
            self._limit_spin.setValue(settings.get('limit', 50))
            self._max_items_spin.setValue(settings.get('max_items', 15))
        elif widget_type == 'text':
            self._text_content.setPlainText(settings.get('content', ''))
            self._text_font_size.setValue(settings.get('font_size', 14))
            self._text_bold_btn.setChecked(settings.get('bold', False))
            self._text_italic_btn.setChecked(settings.get('italic', False))
            self._set_text_align(settings.get('align', 'left'))
            self._text_color = settings.get('color', TEXT_PRI)
            self._text_bg_color = settings.get('bg_color', 'transparent')
            self._text_color_preview.setStyleSheet(
                f"background:{self._text_color}; border-radius:3px; border:1px solid {BORDER_LT};")
            bg = self._text_bg_color if self._text_bg_color != 'transparent' else BG_CARD
            self._text_bg_preview.setStyleSheet(
                f"background:{bg}; border-radius:3px; border:1px solid {BORDER_LT};")
        elif widget_type == 'image':
            self._image_path = settings.get('path', '')
            if self._image_path:
                self._image_path_edit.setText(os.path.basename(self._image_path))
            self._image_opacity.setValue(settings.get('opacity', 100))
            self._set_combo(self._image_fit_combo, settings.get('fit', 'contain'))
        elif widget_type == 'map':
            self._manual_markers = list(settings.get('markers',
                                    settings.get('manual_markers', [])))
            self._refresh_marker_list()
            self._territories = list(settings.get('territories', []))
            self._refresh_territory_list()
            vm = settings.get('view_mode', 'point')
            if hasattr(self, '_view_mode_btns') and vm in self._view_mode_btns:
                self._set_view_mode(vm)
            if hasattr(self, '_area_radius_spin'):
                self._area_radius_spin.setValue(int(settings.get('area_radius', 1000)))
            lm = settings.get('label_mode', 'name')
            if hasattr(self, '_map_label_btns') and lm in self._map_label_btns:
                self._set_map_label_mode(lm)
            ik = settings.get('icon_style', 'pin')
            if hasattr(self, '_map_icon_btns') and ik in self._map_icon_btns:
                self._set_map_icon(ik)

        color = settings.get('color', self._kpi_color)
        self._kpi_color = self._chart_color = color
        self._color_preview.setStyleSheet(
            f"background:{color}; border-radius:4px; border:1px solid {BORDER_LT};")
        if widget_type not in ('text', 'image'):
            self._title_edit.setText(settings.get('title', ''))

        if hasattr(self, '_dataset_combo'):
            idx = self._dataset_combo.findData(settings.get('dataset_name', ''))
            if idx >= 0:
                self._dataset_combo.setCurrentIndex(idx)

        self._update_preview()

    def _set_combo(self, combo: QComboBox, data_value: str):
        idx = combo.findData(data_value)
        if idx < 0: idx = combo.findText(data_value)
        if idx >= 0: combo.setCurrentIndex(idx)


# ─── Диалог предпросмотра / редактора карты ──────────────────────────────────

class MapPreviewDialog(QDialog):
    """
    Показывает Leaflet-карту в отдельном окне.
    editable=True — включает Leaflet.draw для рисования территорий.
    """

    def __init__(self, settings: dict = None, editable: bool = False, parent=None):
        super().__init__(parent)
        self._settings  = settings or {}
        self._editable  = editable
        self._polygons  = list(self._settings.get('territories', []))
        self._view      = None

        self.setWindowTitle("Редактор карты" if editable else "Карта")
        self.setModal(True)
        self.setMinimumSize(720, 520)
        self.resize(860, 620)
        self.setStyleSheet(f"QDialog{{background:{BG_DARK};}}")

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        if self._editable:
            hint = QLabel(
                "Используйте панель инструментов на карте, чтобы нарисовать территории. "
                "Нажмите «Сохранить территории» когда закончите."
            )
            hint.setWordWrap(True)
            hint.setStyleSheet(
                f"font-size:11px; color:{TEXT_MUT}; background:{BG_PANEL};"
                f" border:1px solid {BORDER}; border-radius:5px; padding:7px 10px;"
            )
            root.addWidget(hint)

        if _HAS_WEBENGINE:
            from widgets.dashboard.map_widget import _build_map_html
            self._view = QWebEngineView()
            self._view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            root.addWidget(self._view, 1)

            lat  = self._settings.get('lat')
            lon  = self._settings.get('lon')
            city = self._settings.get('city', '')
            st   = self._settings.get('street', '')
            hs   = self._settings.get('house', '')
            addr = ', '.join(p for p in [hs, st, city] if p) or 'Метка'

            html = _build_map_html(
                markers            = self._settings.get('markers',
                                         self._settings.get('manual_markers', [])),
                territories        = self._polygons,
                editable           = self._editable,
                view_mode          = self._settings.get('view_mode', 'point'),
                default_label_mode = self._settings.get('label_mode', 'name'),
                default_icon       = self._settings.get('icon_style', 'pin'),
                lat                = self._settings.get('lat'),
                lon                = self._settings.get('lon'),
                address_label      = ', '.join(
                    p for p in [self._settings.get('house',''),
                                self._settings.get('street',''),
                                self._settings.get('city','')] if p),
            )
            self._view.setHtml(html, QUrl("about:blank"))
        else:
            no_web = QLabel(
                "QWebEngineView не установлен.\n"
                "Для отображения карты выполните:\n\npip install PySide6-WebEngine"
            )
            no_web.setAlignment(Qt.AlignCenter)
            no_web.setStyleSheet(f"font-size:13px; color:{TEXT_MUT};")
            root.addWidget(no_web, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        if self._editable:
            save_btn = QPushButton("✓ Сохранить территории")
            save_btn.setFixedHeight(36)
            save_btn.setStyleSheet(
                f"QPushButton{{background:{ACCENT_DARK};color:{TEXT_PRI};"
                f"border:none;border-radius:6px;font-size:13px;font-weight:bold;"
                f"padding:0 18px;}}"
                f"QPushButton:hover{{background:{ACCENT};}}"
            )
            save_btn.clicked.connect(self._save_and_close)
            btn_row.addWidget(save_btn)

        close_btn = QPushButton("Закрыть")
        close_btn.setFixedHeight(36)
        close_btn.setStyleSheet(
            f"QPushButton{{background:{BG_CARD};border:1px solid {BORDER};"
            f"border-radius:6px;color:{TEXT_SEC};font-size:13px;padding:0 16px;}}"
            f"QPushButton:hover{{border-color:{BORDER_LT};color:{TEXT_PRI};}}"
        )
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

    def _save_and_close(self):
        if self._view is not None:
            def _on_result(result):
                if result:
                    import json as _json
                    try:
                        self._polygons = _json.loads(result)
                    except Exception:
                        pass
                self.accept()
            self._view.page().runJavaScript(
                "JSON.stringify(window._drawnPolygons || [])", _on_result
            )
        else:
            self.accept()

    def get_territories(self) -> list:
        return self._polygons


# ─── Вспомогательные функции (модульные) ──────────────────────────────────────

def _lbl(text: str, small: bool = False) -> QLabel:
    lbl = QLabel(text)
    if small:
        lbl.setStyleSheet(f"font-size:11px; color:{TEXT_MUT}; background:transparent;")
    else:
        lbl.setStyleSheet(_LABEL_STYLE)
    return lbl

def _color_swatch(color: str) -> QLabel:
    lbl = QLabel()
    lbl.setFixedSize(24, 20)
    lbl.setStyleSheet(f"background:{color}; border-radius:3px; border:1px solid {BORDER_LT};")
    return lbl

def _small_btn(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet(
        f"QPushButton{{background:{BG_CARD};border:1px solid {BORDER};border-radius:4px;"
        f"padding:2px 10px;font-size:11px;color:{TEXT_SEC};}}"
        f"QPushButton:hover{{border-color:{BORDER_ACC};color:{ACCENT};}}"
    )
    return btn
