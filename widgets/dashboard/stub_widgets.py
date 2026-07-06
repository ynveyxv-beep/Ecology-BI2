# widgets/dashboard/stub_widgets.py
"""
BUG 2 FIX: Stub implementations for gauge, progress, and pivot widget types.
These prevent the "неизвестный тип виджета" error when these types are selected
in the creation dialog.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import QLabel, QVBoxLayout, QProgressBar, QSizePolicy

from widgets.dashboard.base_widget import BaseDashboardWidget


class GaugeWidget(BaseDashboardWidget):
    """
    Stub gauge widget — displays a circular progress indicator drawn with QPainter.
    Settings:
        value  (str/float) — 0..100 percentage value
        title  (str)       — label below the gauge
        color  (str)       — accent colour HEX
    """

    def __init__(self, settings: dict = None, parent=None):
        self._gauge_label = QLabel()
        self._gauge_label.setAlignment(Qt.AlignCenter)
        self._gauge_label.setMinimumHeight(80)
        super().__init__(settings, parent)
        self._content_layout.addWidget(self._gauge_label)

    def _apply_settings(self):
        raw   = self._settings.get('value', '0')
        color = self._settings.get('color', '#38BDF8')
        try:
            pct = max(0.0, min(100.0, float(raw)))
        except (ValueError, TypeError):
            pct = 0.0

        # Build a simple SVG arc gauge
        size   = 100
        cx, cy = size // 2, size // 2
        r      = 38
        stroke = 8
        # full circle background arc
        bg_color = '#334155'
        # foreground arc: sweep from -135° to -135° + pct/100 * 270°
        import math
        start_angle = -135.0
        sweep       = pct / 100.0 * 270.0

        def arc_path(cx, cy, r, start_deg, sweep_deg):
            """Return SVG arc path string for a partial circle."""
            start_rad  = math.radians(start_deg)
            end_rad    = math.radians(start_deg + sweep_deg)
            x1 = cx + r * math.cos(start_rad)
            y1 = cy + r * math.sin(start_rad)
            x2 = cx + r * math.cos(end_rad)
            y2 = cy + r * math.sin(end_rad)
            large = 1 if abs(sweep_deg) > 180 else 0
            sweep_flag = 1 if sweep_deg > 0 else 0
            return f"M {x1:.2f} {y1:.2f} A {r} {r} 0 {large} {sweep_flag} {x2:.2f} {y2:.2f}"

        bg_path  = arc_path(cx, cy, r, start_angle, 270)
        fg_path  = arc_path(cx, cy, r, start_angle, sweep) if pct > 0 else ''

        fg_el = (f'<path d="{fg_path}" fill="none" stroke="{color}" '
                 f'stroke-width="{stroke}" stroke-linecap="round"/>'
                 ) if fg_path else ''

        text_y = cy + 6
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">'
            f'<path d="{bg_path}" fill="none" stroke="{bg_color}" '
            f'stroke-width="{stroke}" stroke-linecap="round"/>'
            f'{fg_el}'
            f'<text x="{cx}" y="{text_y}" text-anchor="middle" '
            f'font-family="sans-serif" font-size="16" font-weight="bold" '
            f'fill="{color}">{pct:.0f}%</text>'
            f'</svg>'
        )

        from PySide6.QtCore import QByteArray
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtGui import QPixmap

        pix = QPixmap(size, size)
        pix.fill(QColor('transparent'))
        renderer = QSvgRenderer(QByteArray(svg.encode('utf-8')))
        if renderer.isValid():
            painter = QPainter(pix)
            painter.setRenderHint(QPainter.Antialiasing)
            renderer.render(painter)
            painter.end()
        self._gauge_label.setPixmap(pix)
        self._gauge_label.setStyleSheet("background: transparent;")


class ProgressWidget(BaseDashboardWidget):
    """
    Stub progress widget — displays one or more horizontal progress bars.
    Settings:
        value  (str/float) — 0..100 percentage value
        title  (str)       — widget label
        color  (str)       — bar colour HEX
    """

    def __init__(self, settings: dict = None, parent=None):
        self._bar   = None
        self._label = None
        super().__init__(settings, parent)
        if self._bar is None:
            self._label = QLabel()
            self._label.setAlignment(Qt.AlignCenter)
            self._bar = QProgressBar()
            self._bar.setRange(0, 100)
            self._bar.setTextVisible(True)
            self._bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self._content_layout.addWidget(self._label)
            self._content_layout.addWidget(self._bar)
        self._apply_settings()

    def _apply_settings(self):
        if self._bar is None:
            return
        raw   = self._settings.get('value', '0')
        color = self._settings.get('color', '#38BDF8')
        title = self._settings.get('title', '')
        try:
            pct = max(0, min(100, int(float(raw))))
        except (ValueError, TypeError):
            pct = 0

        self._bar.setValue(pct)
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                background: #334155;
                border: none;
                border-radius: 5px;
                height: 20px;
                text-align: center;
                color: #F1F5F9;
                font-size: 12px;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 5px;
            }}
        """)
        if self._label:
            self._label.setText(title)
            self._label.setStyleSheet(f"font-size:12px; color:#94A3B8; background:transparent;")


class PivotWidget(BaseDashboardWidget):
    """
    Stub pivot (summary) widget — shows basic dataset statistics as text.
    Settings:
        title        (str) — widget label
        dataset_name (str) — dataset to summarise
        value        (str) — fallback text if no dataset loaded
    """

    def __init__(self, settings: dict = None, parent=None):
        self._text_label = QLabel()
        self._text_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self._text_label.setWordWrap(True)
        self._text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        super().__init__(settings, parent)
        self._content_layout.addWidget(self._text_label)

    def _apply_settings(self):
        color = self._settings.get('color', '#38BDF8')
        val   = self._settings.get('value', '')

        if self._df is not None:
            try:
                rows = len(self._df)
                cols = len(self._df.columns)
                num_cols = self._df.select_dtypes(include='number').columns.tolist()
                lines = [
                    f"<b>Строк:</b> {rows}",
                    f"<b>Столбцов:</b> {cols}",
                ]
                for col in num_cols[:4]:
                    mn  = round(float(self._df[col].mean()),   2)
                    mx  = round(float(self._df[col].max()),    2)
                    lines.append(f"<b>{col}:</b> avg {mn}, max {mx}")
                text = "<br>".join(lines)
            except Exception:
                text = val or "Нет данных"
        else:
            text = val or "<span style='color:#64748B;'>Загрузите датасет</span>"

        self._text_label.setText(
            f"<div style='font-size:12px; color:#F1F5F9; padding:4px;'>{text}</div>"
        )
