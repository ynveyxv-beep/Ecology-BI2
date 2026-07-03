# widgets/dialogs/marker_editor_dialog.py
"""
Диалог добавления / редактирования маркера карты.
Поддерживает: геокодирование адреса, стиль иконки, режим подписи, цвет, значение/статус.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QFrame,
    QPushButton, QLabel, QLineEdit, QDoubleSpinBox, QSpinBox,
    QComboBox, QTextEdit, QWidget, QColorDialog
)
from PySide6.QtGui import QColor

from ui.theme import (
    BG_DARK, BG_PANEL, BG_CARD, BG_HOVER, BG_ACTIVE,
    BORDER, BORDER_LT, BORDER_ACC,
    ACCENT, ACCENT_DARK, ACCENT_RED,
    TEXT_PRI, TEXT_SEC, TEXT_MUT,
    RADIUS_SM, scrollbar_style,
)

_STATUS_COLORS = {
    'норма':       '#4caf50',
    'превышение':  '#fbbf24',
    'критично':    '#f87171',
}

LABEL_MODES = [
    ('name',   'Своё название'),
    ('address','Адрес'),
    ('coords', 'Координаты'),
    ('none',   'Без подписи'),
]

ICON_STYLES = [
    ('pin',    '● Булавка'),
    ('circle', '○ Кружок'),
    ('pulse',  '◎ Пульс'),
    ('star',   '★ Звезда'),
    ('flag',   '⚑ Флажок'),
    ('dot',    '· Точка'),
]

_STYLE = f"""
QDialog {{ background:{BG_DARK}; color:{TEXT_PRI}; }}
QLabel  {{ color:{TEXT_SEC}; font-size:11px; background:transparent; }}
QLineEdit, QDoubleSpinBox, QComboBox, QTextEdit {{
    background:{BG_CARD}; border:1px solid {BORDER};
    border-radius:{RADIUS_SM}; color:{TEXT_PRI};
    padding:5px 8px; font-size:12px;
    selection-background-color:{ACCENT_DARK};
}}
QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus {{
    border-color:{ACCENT};
}}
QComboBox::drop-down {{ border:none; padding-right:6px; }}
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background:{BG_HOVER}; border:none; width:16px;
}}
QScrollArea {{ background:transparent; border:none; }}
{scrollbar_style()}
"""

_BTN_PRIMARY = f"""
QPushButton {{
    background:{ACCENT_DARK}; color:#0F172A; border:none;
    border-radius:{RADIUS_SM}; padding:7px 20px;
    font-weight:600; font-size:12px;
}}
QPushButton:hover {{ background:{ACCENT}; }}
"""
_BTN_SECONDARY = f"""
QPushButton {{
    background:{BG_CARD}; color:{TEXT_SEC};
    border:1px solid {BORDER}; border-radius:{RADIUS_SM};
    padding:7px 18px; font-size:12px;
}}
QPushButton:hover {{ background:{BG_HOVER}; border-color:{BORDER_LT}; color:{TEXT_PRI}; }}
"""
_BTN_TOGGLE = f"""
QPushButton {{
    background:{BG_CARD}; border:1px solid {BORDER};
    border-radius:4px; padding:4px 10px;
    font-size:11px; color:{TEXT_SEC};
}}
QPushButton:hover   {{ background:{BG_HOVER}; border-color:{BORDER_LT}; }}
QPushButton:checked {{ background:{BG_ACTIVE}; border-color:{ACCENT}; color:{ACCENT}; font-weight:bold; }}
"""


class MarkerEditorDialog(QDialog):
    """Диалог для ввода данных одного маркера карты."""

    def __init__(self, marker: dict = None, parent=None):
        super().__init__(parent)
        self._marker      = marker or {}
        self._marker_color = marker.get('color', '#4caf50') if marker else '#4caf50'
        self._geo_lat     = marker.get('lat') if marker else None
        self._geo_lon     = (marker.get('lon') or marker.get('lng')) if marker else None

        self.setWindowTitle("Маркер" if not marker else "Редактировать маркер")
        self.setMinimumWidth(420)
        self.setModal(True)
        self.setStyleSheet(_STYLE)
        self._build_ui()
        self._fill_fields()

    # ─── UI ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        # Заголовок
        title_lbl = QLabel("Новый маркер" if not self._marker else "Редактировать маркер")
        title_lbl.setStyleSheet(f"font-size:15px;font-weight:600;color:{TEXT_PRI};")
        root.addWidget(title_lbl)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background:{BORDER};max-height:1px;")
        root.addWidget(sep)

        # ── Геокодирование адреса ─────────────────────────────────────────────
        addr_frame = QFrame()
        addr_frame.setStyleSheet(
            f"QFrame{{background:{BG_PANEL};border:1px solid {BORDER};"
            f"border-radius:6px;}}QLabel{{background:transparent;}}"
        )
        addr_lay = QVBoxLayout(addr_frame)
        addr_lay.setContentsMargins(10, 10, 10, 10)
        addr_lay.setSpacing(6)

        hint = QLabel("Введите адрес для автоматического определения координат:")
        hint.setStyleSheet(f"font-size:11px;color:{TEXT_MUT};background:transparent;")
        addr_lay.addWidget(hint)

        addr_form = QFormLayout()
        addr_form.setSpacing(6)
        addr_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self._city_edit   = QLineEdit(); self._city_edit.setPlaceholderText("Город / нас. пункт")
        self._street_edit = QLineEdit(); self._street_edit.setPlaceholderText("Улица")
        self._house_edit  = QLineEdit(); self._house_edit.setPlaceholderText("Дом")
        addr_form.addRow("Нас. пункт:", self._city_edit)
        addr_form.addRow("Улица:",      self._street_edit)
        addr_form.addRow("Дом:",        self._house_edit)
        addr_lay.addLayout(addr_form)

        geo_row = QHBoxLayout(); geo_row.setSpacing(8)
        self._geo_btn = QPushButton("🔍 Найти координаты")
        self._geo_btn.setStyleSheet(
            f"QPushButton{{background:{BG_CARD};border:1px solid {BORDER_ACC};"
            f"border-radius:5px;color:{ACCENT};padding:4px 12px;font-size:11px;}}"
            f"QPushButton:hover{{background:{BG_ACTIVE};}}"
        )
        self._geo_btn.clicked.connect(self._geocode)
        geo_row.addWidget(self._geo_btn)

        self._geo_lbl = QLabel("")
        self._geo_lbl.setWordWrap(True)
        self._geo_lbl.setStyleSheet(f"font-size:10px;color:{TEXT_MUT};background:transparent;")
        geo_row.addWidget(self._geo_lbl, 1)
        addr_lay.addLayout(geo_row)
        root.addWidget(addr_frame)

        # ── Название и координаты ─────────────────────────────────────────────
        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Название точки")
        form.addRow("Название:", self.name_edit)

        coord_w = QWidget(); coord_l = QHBoxLayout(coord_w)
        coord_l.setContentsMargins(0, 0, 0, 0); coord_l.setSpacing(8)
        self.lat_spin = QDoubleSpinBox()
        self.lat_spin.setRange(50.0, 60.0); self.lat_spin.setDecimals(6)
        self.lat_spin.setSingleStep(0.001); self.lat_spin.setValue(56.3269)
        self.lat_spin.setPrefix("Ш: ")
        self.lng_spin = QDoubleSpinBox()
        self.lng_spin.setRange(39.0, 50.0); self.lng_spin.setDecimals(6)
        self.lng_spin.setSingleStep(0.001); self.lng_spin.setValue(44.0059)
        self.lng_spin.setPrefix("Д: ")
        coord_l.addWidget(self.lat_spin); coord_l.addWidget(self.lng_spin)
        form.addRow("Координаты:", coord_w)

        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(0, 100000)
        self.radius_spin.setSingleStep(100)
        self.radius_spin.setSuffix(" м")
        self.radius_spin.setSpecialValueText("Нет")
        self.radius_spin.setValue(0)
        self.radius_spin.setToolTip("Радиус зоны вокруг точки (0 = не показывать)")
        form.addRow("Радиус зоны:", self.radius_spin)

        root.addLayout(form)

        # ── Стиль иконки ─────────────────────────────────────────────────────
        root.addWidget(self._section_lbl("Иконка:"))
        icon_row = QHBoxLayout(); icon_row.setSpacing(5)
        self._icon_btns = {}
        for key, label in ICON_STYLES:
            btn = QPushButton(label); btn.setCheckable(True)
            btn.setStyleSheet(_BTN_TOGGLE)
            btn.clicked.connect(lambda _, k=key: self._set_icon(k))
            icon_row.addWidget(btn)
            self._icon_btns[key] = btn
        icon_row.addStretch()
        root.addLayout(icon_row)
        self._icon_key = self._marker.get('icon', 'pin')
        self._icon_btns[self._icon_key].setChecked(True)

        # ── Режим подписи ────────────────────────────────────────────────────
        root.addWidget(self._section_lbl("Подпись:"))
        lbl_row = QHBoxLayout(); lbl_row.setSpacing(5)
        self._label_btns = {}
        for key, label in LABEL_MODES:
            btn = QPushButton(label); btn.setCheckable(True)
            btn.setStyleSheet(_BTN_TOGGLE)
            btn.clicked.connect(lambda _, k=key: self._set_label_mode(k))
            lbl_row.addWidget(btn)
            self._label_btns[key] = btn
        lbl_row.addStretch()
        root.addLayout(lbl_row)
        self._label_mode = self._marker.get('label_mode', 'name')
        self._label_btns[self._label_mode].setChecked(True)

        # ── Цвет маркера ─────────────────────────────────────────────────────
        color_row = QHBoxLayout(); color_row.setSpacing(10)
        color_row.addWidget(self._section_lbl("Цвет:"))
        self._color_swatch = QLabel()
        self._color_swatch.setFixedSize(26, 20)
        self._color_swatch.setStyleSheet(
            f"background:{self._marker_color};border-radius:4px;border:1px solid {BORDER_LT};"
        )
        color_row.addWidget(self._color_swatch)
        pick_btn = QPushButton("Выбрать"); pick_btn.setStyleSheet(_BTN_SECONDARY)
        pick_btn.setFixedHeight(28)
        pick_btn.clicked.connect(self._pick_color)
        color_row.addWidget(pick_btn)
        color_row.addStretch()
        root.addLayout(color_row)

        # ── Значение и статус ────────────────────────────────────────────────
        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"background:{BORDER};max-height:1px;")
        root.addWidget(sep2)

        form2 = QFormLayout()
        form2.setSpacing(8); form2.setLabelAlignment(Qt.AlignRight)
        form2.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        val_w = QWidget(); val_l = QHBoxLayout(val_w)
        val_l.setContentsMargins(0, 0, 0, 0); val_l.setSpacing(8)
        self.value_edit = QLineEdit(); self.value_edit.setPlaceholderText("45.2")
        self.unit_edit  = QLineEdit(); self.unit_edit.setPlaceholderText("мкг/м³")
        self.unit_edit.setMaximumWidth(90)
        val_l.addWidget(self.value_edit); val_l.addWidget(self.unit_edit)
        form2.addRow("Значение:", val_w)

        self.status_combo = QComboBox()
        for s in _STATUS_COLORS: self.status_combo.addItem(s)
        self.status_combo.currentTextChanged.connect(self._update_status_indicator)
        form2.addRow("Статус:", self.status_combo)

        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Заметка (необязательно)...")
        self.note_edit.setMaximumHeight(56)
        form2.addRow("Заметка:", self.note_edit)

        root.addLayout(form2)

        self._status_bar = QLabel()
        self._status_bar.setFixedHeight(3)
        self._status_bar.setStyleSheet(
            f"background:{_STATUS_COLORS['норма']};border-radius:1px;"
        )
        root.addWidget(self._status_bar)

        # ── Кнопки ───────────────────────────────────────────────────────────
        btn_row = QHBoxLayout(); btn_row.addStretch()
        cancel_btn = QPushButton("Отмена"); cancel_btn.setStyleSheet(_BTN_SECONDARY)
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton("Сохранить"); ok_btn.setStyleSheet(_BTN_PRIMARY)
        ok_btn.setDefault(True); ok_btn.clicked.connect(self._on_accept)
        btn_row.addWidget(cancel_btn); btn_row.addWidget(ok_btn)
        root.addLayout(btn_row)

    # ─── Вспомогательные ─────────────────────────────────────────────────────

    def _section_lbl(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size:11px;font-weight:600;color:{TEXT_SEC};background:transparent;")
        return lbl

    def _set_icon(self, key: str):
        self._icon_key = key
        for k, b in self._icon_btns.items(): b.setChecked(k == key)

    def _set_label_mode(self, key: str):
        self._label_mode = key
        for k, b in self._label_btns.items(): b.setChecked(k == key)

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self._marker_color), self)
        if c.isValid():
            self._marker_color = c.name()
            self._color_swatch.setStyleSheet(
                f"background:{c.name()};border-radius:4px;border:1px solid {BORDER_LT};"
            )

    def _update_status_indicator(self, status: str):
        color = _STATUS_COLORS.get(status, _STATUS_COLORS['норма'])
        self._status_bar.setStyleSheet(f"background:{color};border-radius:1px;")

    def _fill_fields(self):
        m = self._marker
        if not m:
            return
        self.name_edit.setText(m.get('name', ''))
        if m.get('lat') is not None:
            self.lat_spin.setValue(float(m['lat']))
        lon = m.get('lon') or m.get('lng')
        if lon is not None:
            self.lng_spin.setValue(float(lon))
        self.value_edit.setText(str(m.get('value', '')))
        self.unit_edit.setText(m.get('unit', ''))
        self.note_edit.setPlainText(m.get('note', ''))
        status = m.get('status', 'норма')
        idx = self.status_combo.findText(status)
        if idx >= 0: self.status_combo.setCurrentIndex(idx)
        self._update_status_indicator(status)
        # Address fields
        self._city_edit.setText(m.get('city', ''))
        self._street_edit.setText(m.get('street', ''))
        self._house_edit.setText(m.get('house', ''))
        if m.get('lat') and m.get('lon'):
            self._geo_lbl.setText(f"✅ {m['lat']:.5f}, {m.get('lon', m.get('lng', 0)):.5f}")
            self._geo_lbl.setStyleSheet(f"font-size:10px;color:{ACCENT};background:transparent;")
        # Radius
        self.radius_spin.setValue(int(m.get('radius', 0)))

    # ─── Геокодирование ───────────────────────────────────────────────────────

    def _geocode(self):
        city   = self._city_edit.text().strip()
        street = self._street_edit.text().strip()
        house  = self._house_edit.text().strip()
        parts  = [p for p in [house, street, city, 'Нижегородская область', 'Россия'] if p]
        if len(parts) <= 2:
            self._geo_lbl.setText("⚠ Введите хотя бы населённый пункт")
            self._geo_lbl.setStyleSheet(f"font-size:10px;color:{ACCENT_RED};background:transparent;")
            return

        self._geo_lbl.setText("⏳ Поиск…")
        self._geo_lbl.setStyleSheet(f"font-size:10px;color:{TEXT_MUT};background:transparent;")

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
                self.lat_spin.setValue(self._geo_lat)
                self.lng_spin.setValue(self._geo_lon)
                short = data[0].get('display_name', '')[:50]
                self._geo_lbl.setText(f"✅ {short}…")
                self._geo_lbl.setStyleSheet(f"font-size:10px;color:{ACCENT};background:transparent;")
                # Auto-fill name if empty
                if not self.name_edit.text():
                    self.name_edit.setText(', '.join(p for p in [house, street, city] if p))
            else:
                self._geo_lbl.setText("❌ Адрес не найден")
                self._geo_lbl.setStyleSheet(f"font-size:10px;color:{ACCENT_RED};background:transparent;")
        except Exception:
            self._geo_lbl.setText("⚠ Ошибка соединения")
            self._geo_lbl.setStyleSheet(f"font-size:10px;color:{TEXT_MUT};background:transparent;")

    # ─── Принять ─────────────────────────────────────────────────────────────

    def _on_accept(self):
        if not self.name_edit.text().strip():
            self.name_edit.setPlaceholderText("⚠ Введите название")
            self.name_edit.setStyleSheet(
                self.name_edit.styleSheet() + f"border-color:{ACCENT_RED};"
            )
            return
        self.accept()

    def get_marker_data(self) -> dict:
        """Возвращает dict с данными маркера. Вызывать после accept()."""
        return {
            'name':       self.name_edit.text().strip(),
            'lat':        round(self.lat_spin.value(), 6),
            'lon':        round(self.lng_spin.value(), 6),
            'lng':        round(self.lng_spin.value(), 6),  # backward compat
            'city':       self._city_edit.text().strip(),
            'street':     self._street_edit.text().strip(),
            'house':      self._house_edit.text().strip(),
            'label_mode': self._label_mode,
            'icon':       self._icon_key,
            'color':      self._marker_color,
            'value':      self.value_edit.text().strip(),
            'unit':       self.unit_edit.text().strip(),
            'status':     self.status_combo.currentText(),
            'note':       self.note_edit.toPlainText().strip(),
            'radius':     self.radius_spin.value(),
        }
