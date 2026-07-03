# widgets/dashboard/chart_widget.py
"""
Виджет-график на основе matplotlib.
Поддерживает 7 типов: bar, line, area, radar, scatter, heatmap, treemap.
Тёмная природная тема.
"""

import numpy as np
import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy

from widgets.dashboard.base_widget import BaseDashboardWidget
from ui.theme import (
    BG_CARD, BG_DARK, BORDER, TEXT_PRI, TEXT_SEC, TEXT_MUT,
    ACCENT, CHART_PALETTE
)

# ─── Цвета для matplotlib ────────────────────────────────────────────────────

_FIG_BG   = BG_CARD
_AX_BG    = BG_DARK
_TICK_CLR = TEXT_SEC
_GRID_CLR = BORDER
_TITLE_CLR = TEXT_PRI


def _style_axes(ax, fig):
    """Применяет тёмную тему к осям."""
    fig.patch.set_facecolor(_FIG_BG)
    ax.set_facecolor(_AX_BG)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)
        spine.set_linewidth(0.8)
    ax.tick_params(colors=_TICK_CLR, labelsize=8)
    ax.xaxis.label.set_color(TEXT_SEC)
    ax.yaxis.label.set_color(TEXT_SEC)
    ax.title.set_color(_TITLE_CLR)


# ─── Реализация treemap без squarify ──────────────────────────────────────────

def _treemap_rects(values, x=0.0, y=0.0, w=1.0, h=1.0):
    """Slice-and-dice treemap — возвращает список (x, y, w, h)."""
    if not values:
        return []
    total = sum(values)
    if total == 0 or len(values) == 0:
        return []
    if len(values) == 1:
        return [(x, y, w, h)]

    rects = []
    if w >= h:
        # разбиваем по горизонтали
        half = total / 2
        s, split = 0, len(values)
        for i, v in enumerate(values):
            s += v
            if s >= half:
                split = i + 1
                break
        left  = values[:split]
        right = values[split:]
        ratio = sum(left) / total
        rects += _treemap_rects(left,  x,         y, w * ratio, h)
        rects += _treemap_rects(right, x + w * ratio, y, w * (1 - ratio), h)
    else:
        # разбиваем по вертикали
        half = total / 2
        s, split = 0, len(values)
        for i, v in enumerate(values):
            s += v
            if s >= half:
                split = i + 1
                break
        bot = values[:split]
        top = values[split:]
        ratio = sum(bot) / total
        rects += _treemap_rects(bot, x, y,         w, h * ratio)
        rects += _treemap_rects(top, x, y + h * ratio, w, h * (1 - ratio))
    return rects


# ─── Главный виджет ───────────────────────────────────────────────────────────

class ChartWidget(BaseDashboardWidget):
    """График: 7 типов, тёмная тема, реальные данные из датасетов."""

    def __init__(self, settings: dict = None, parent=None):
        self._canvas = None
        super().__init__(settings, parent)

    # ─── Применение настроек ──────────────────────────────────────────────

    def _apply_settings(self):
        s = self._settings
        data_source  = s.get('data_source', 'none')
        chart_style  = s.get('chart_style', 'bar')
        color        = s.get('color', ACCENT)
        show_grid    = s.get('show_grid', True)
        show_values  = s.get('show_values', False)
        max_items    = int(s.get('max_items', 15))
        title        = s.get('title', '')

        # Очищаем старые виджеты
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._canvas = None

        labels, values = self._resolve_data(data_source, max_items)
        if labels is None or data_source == 'none' or not values:
            labels, values = self._demo_data(chart_style, data_source)

        self._render(labels, values, chart_style, color,
                     show_grid, show_values, title)

    # ─── Данные ───────────────────────────────────────────────────────────

    def _resolve_data(self, data_source, max_items):
        if self._df is None or data_source == 'none':
            return None, None
        try:
            from eco_modules import eco_metrics as em
            import pandas as pd

            if data_source == 'by_category':
                raw = em.get_by_category(self._df)
            elif data_source == 'by_omsu':
                raw = em.get_by_omsu(self._df)
            elif data_source == 'by_mro':
                raw = em.get_by_mro(self._df)
            elif data_source.startswith('time_series_'):
                freq = data_source.split('_')[-1]
                raw  = em.get_time_series(self._df, freq)
            else:
                # Пробуем взять числовые колонки напрямую
                num_cols = self._df.select_dtypes(include='number').columns.tolist()
                if not num_cols:
                    return [], []
                col = self._settings.get('y_column', num_cols[0])
                label_col = self._settings.get('x_column', self._df.columns[0])
                raw = self._df[[label_col, col]].dropna()
                raw = raw.set_index(label_col)[col]
                raw = raw.sort_values(ascending=False).head(max_items)

            if raw is None or len(raw) == 0:
                return [], []

            if isinstance(raw, pd.Series):
                if data_source.startswith('time_series'):
                    raw = raw.sort_index()
                else:
                    raw = raw.sort_values(ascending=False).head(max_items)
                labels = [str(i) for i in raw.index]
                if data_source.startswith('time_series'):
                    try:
                        freq_code = data_source.split('_')[-1]
                        fmt = '%d.%m' if freq_code == 'D' else '%b %Y'
                        labels = [pd.to_datetime(i).strftime(fmt) for i in raw.index]
                    except Exception:
                        pass
                return labels, [float(v) for v in raw.values]

            elif isinstance(raw, dict):
                items = sorted(raw.items(), key=lambda x: x[1], reverse=True)[:max_items]
                return [str(k) for k, _ in items], [float(v) for _, v in items]

            return [], []
        except Exception as e:
            print(f"ChartWidget data error: {e}")
            return [], []

    def _demo_data(self, chart_style, data_source='none'):
        """Демо-данные в зависимости от типа графика."""
        if chart_style == 'radar':
            labels = ['Воздух', 'Вода', 'Почва', 'Шум', 'Лес', 'Отходы']
            values = [72.0, 88.0, 55.0, 63.0, 91.0, 45.0]
        elif chart_style == 'scatter':
            np.random.seed(42)
            labels = [str(i) for i in range(30)]
            values = np.random.normal(50, 20, 30).clip(5, 100).tolist()
        elif chart_style == 'heatmap':
            labels = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн']
            values = [12.0, 18.0, 15.0, 22.0, 19.0, 25.0]
        elif chart_style == 'treemap':
            labels = ['Мусор', 'Водоёмы', 'Воздух', 'Почва', 'Шум', 'Прочее']
            values = [48.0, 31.0, 22.0, 17.0, 14.0, 8.0]
        elif data_source and data_source.startswith('time_series'):
            labels = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг']
            values = [12.0, 18.0, 15.0, 22.0, 19.0, 25.0, 21.0, 28.0]
        else:
            labels = ['Мусор', 'Водоёмы', 'Воздух', 'Почва', 'Шум', 'Прочее']
            values = [48.0, 31.0, 22.0, 17.0, 14.0, 8.0]
        return labels, values

    # ─── Рендеринг ────────────────────────────────────────────────────────

    def _render(self, labels, values, chart_style, color,
                show_grid, show_values, title):
        if not values:
            self._show_no_data()
            return

        fig = Figure(figsize=(4, 3), tight_layout=True)
        fig.patch.set_facecolor(_FIG_BG)

        if chart_style == 'radar':
            self._render_radar(fig, labels, values, color, title, show_grid)
        elif chart_style == 'scatter':
            self._render_scatter(fig, labels, values, color, title, show_grid)
        elif chart_style == 'heatmap':
            self._render_heatmap(fig, labels, values, title)
        elif chart_style == 'treemap':
            self._render_treemap(fig, labels, values, title)
        else:
            self._render_standard(fig, labels, values, chart_style, color,
                                  show_grid, show_values, title)

        canvas = FigureCanvasQTAgg(fig)
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        canvas.setStyleSheet(f"background: {_FIG_BG};")
        self._canvas = canvas
        self._content_layout.addWidget(canvas)

    # ── Стандартные (bar / line / area) ──────────────────────────────────

    def _render_standard(self, fig, labels, values, style, color,
                         show_grid, show_values, title):
        ax = fig.add_subplot(111)
        _style_axes(ax, fig)

        x = np.arange(len(values))
        y = np.array(values, dtype=float)

        alpha_fill = 'B0'  # ~70%
        if style == 'bar':
            bars = ax.bar(x, y, color=color + alpha_fill, edgecolor=color,
                          linewidth=0.6, width=0.65)
            if show_values:
                for bar, val in zip(bars, y):
                    fmt = f'{int(val):,}' if val == int(val) else f'{val:.1f}'
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                            fmt, ha='center', va='bottom', fontsize=7,
                            color=TEXT_PRI)
        elif style == 'area':
            ax.fill_between(x, y, alpha=0.35, color=color)
            ax.plot(x, y, color=color, linewidth=2, marker='o',
                    markersize=4, markerfacecolor=color)
        else:  # line
            ax.plot(x, y, color=color, linewidth=2, marker='o',
                    markersize=4, markerfacecolor=color, markeredgewidth=0)

        if show_grid:
            ax.yaxis.grid(True, color=_GRID_CLR, linewidth=0.5, alpha=0.5)
            ax.set_axisbelow(True)

        # Подписи категорий
        if style == 'bar' and len(labels) > 0:
            ax.set_xticks(x)
            step = max(1, len(labels) // 8)
            ax.set_xticklabels(
                [labels[i] if i % step == 0 else '' for i in range(len(labels))],
                rotation=35, ha='right', fontsize=7
            )
        elif style in ('line', 'area'):
            ax.set_xticks(x[::max(1, len(x) // 6)])
            ax.set_xticklabels(labels[::max(1, len(labels) // 6)],
                               rotation=30, ha='right', fontsize=7)

        if title:
            ax.set_title(title, color=_TITLE_CLR, fontsize=10, pad=6)

        y_max = y.max() if len(y) else 1.0
        ax.set_ylim(0, y_max * 1.15)
        ax.set_xlim(-0.5, len(x) - 0.5)

    # ── Радар ─────────────────────────────────────────────────────────────

    def _render_radar(self, fig, labels, values, color, title, show_grid):
        N = len(labels)
        if N < 3:
            labels  = labels  + ['—'] * (3 - N)
            values  = values  + [0.0] * (3 - N)
            N = 3

        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        vals   = values + values[:1]
        angs   = angles + angles[:1]

        ax = fig.add_subplot(111, polar=True)
        fig.patch.set_facecolor(_FIG_BG)
        ax.set_facecolor(_AX_BG)

        ax.plot(angs, vals, color=color, linewidth=2, zorder=3)
        ax.fill(angs, vals, color=color, alpha=0.25, zorder=2)

        ax.set_xticks(angles)
        ax.set_xticklabels(labels, color=TEXT_SEC, fontsize=8)
        ax.tick_params(colors=_TICK_CLR, labelsize=7)
        ax.yaxis.set_tick_params(labelcolor=TEXT_MUT, labelsize=6)
        ax.grid(color=_GRID_CLR, linewidth=0.5, alpha=0.6)
        for spine in ax.spines.values():
            spine.set_edgecolor(BORDER)

        if title:
            ax.set_title(title, color=_TITLE_CLR, fontsize=10, pad=14)

    # ── Scatter ───────────────────────────────────────────────────────────

    def _render_scatter(self, fig, labels, values, color, title, show_grid):
        ax = fig.add_subplot(111)
        _style_axes(ax, fig)

        # Для scatter: значения → Y; индекс → X (или две числовые колонки из df)
        y = np.array(values, dtype=float)
        if self._df is not None:
            num_cols = self._df.select_dtypes(include='number').columns.tolist()
            if len(num_cols) >= 2:
                xcol = self._settings.get('x_column', num_cols[0])
                ycol = self._settings.get('y_column', num_cols[1])
                try:
                    x_data = self._df[xcol].dropna().values[:len(y)]
                    y_data = self._df[ycol].dropna().values[:len(y)]
                    ax.scatter(x_data, y_data, color=color, alpha=0.7,
                               edgecolors=color, linewidth=0.5, s=40)
                    ax.set_xlabel(xcol, color=TEXT_SEC, fontsize=8)
                    ax.set_ylabel(ycol, color=TEXT_SEC, fontsize=8)
                    if show_grid:
                        ax.grid(color=_GRID_CLR, linewidth=0.5, alpha=0.5)
                    if title:
                        ax.set_title(title, color=_TITLE_CLR, fontsize=10, pad=6)
                    return
                except Exception:
                    pass

        # Демо: ранг → значение
        x = np.arange(len(y))
        np.random.seed(0)
        jitter = np.random.normal(0, 0.2, len(y))
        ax.scatter(x + jitter, y, color=color, alpha=0.7, s=40,
                   edgecolors=color, linewidth=0.3)
        if show_grid:
            ax.grid(color=_GRID_CLR, linewidth=0.5, alpha=0.5)
        ax.set_xlabel('Индекс', color=TEXT_SEC, fontsize=8)
        ax.set_ylabel('Значение', color=TEXT_SEC, fontsize=8)
        if title:
            ax.set_title(title, color=_TITLE_CLR, fontsize=10, pad=6)

    # ── Heatmap ───────────────────────────────────────────────────────────

    def _render_heatmap(self, fig, labels, values, title):
        ax = fig.add_subplot(111)
        fig.patch.set_facecolor(_FIG_BG)
        ax.set_facecolor(_AX_BG)
        for spine in ax.spines.values():
            spine.set_edgecolor(BORDER)

        # Строим матрицу: если df есть и есть несколько числовых колонок
        if self._df is not None:
            num_cols = self._df.select_dtypes(include='number').columns.tolist()
            if len(num_cols) >= 2:
                try:
                    matrix = self._df[num_cols[:8]].head(12).fillna(0).values.T
                    col_labels = [str(c)[:10] for c in self._df.index[:12]]
                    row_labels = [str(c)[:12] for c in num_cols[:8]]
                    im = ax.imshow(matrix, cmap='YlGn', aspect='auto')
                    ax.set_xticks(range(len(col_labels)))
                    ax.set_xticklabels(col_labels, rotation=35, ha='right',
                                       fontsize=6, color=TEXT_SEC)
                    ax.set_yticks(range(len(row_labels)))
                    ax.set_yticklabels(row_labels, fontsize=7, color=TEXT_SEC)
                    fig.colorbar(im, ax=ax, shrink=0.8,
                                 label='').set_label('', color=TEXT_MUT)
                    if title:
                        ax.set_title(title, color=_TITLE_CLR, fontsize=10, pad=6)
                    return
                except Exception:
                    pass

        # Демо: категории × месяцы
        months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн']
        cats   = labels[:6] if labels else ['A', 'B', 'C', 'D']
        np.random.seed(7)
        matrix = np.random.randint(5, 50, (len(cats), len(months))).astype(float)
        # Вставляем реальные значения в первую строку
        for j, v in enumerate(values[:len(months)]):
            matrix[0, j] = v

        im = ax.imshow(matrix, cmap='YlGn', aspect='auto')
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(months, fontsize=7, color=TEXT_SEC)
        ax.set_yticks(range(len(cats)))
        ax.set_yticklabels(cats, fontsize=7, color=TEXT_SEC)
        ax.tick_params(colors=_TICK_CLR)
        if title:
            ax.set_title(title, color=_TITLE_CLR, fontsize=10, pad=6)

    # ── Treemap ───────────────────────────────────────────────────────────

    def _render_treemap(self, fig, labels, values, title):
        ax = fig.add_subplot(111)
        fig.patch.set_facecolor(_FIG_BG)
        ax.set_facecolor(_FIG_BG)
        ax.axis('off')

        if not values or sum(values) == 0:
            ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center',
                    color=TEXT_MUT, fontsize=12)
            return

        # Сортируем по убыванию
        pairs = sorted(zip(values, labels), reverse=True)
        values_s = [p[0] for p in pairs]
        labels_s = [p[1] for p in pairs]

        rects = _treemap_rects(values_s)
        total = sum(values_s)
        palette = CHART_PALETTE * (len(values_s) // len(CHART_PALETTE) + 1)

        for i, ((x, y, w, h), label, val) in enumerate(
                zip(rects, labels_s, values_s)):
            pct = val / total * 100
            patch = mpatches.FancyBboxPatch(
                (x + 0.005, y + 0.005), w - 0.010, h - 0.010,
                boxstyle='round,pad=0.005',
                facecolor=palette[i], edgecolor=_FIG_BG, linewidth=1.5
            )
            ax.add_patch(patch)
            if w > 0.08 and h > 0.05:
                short_label = label[:14] + '…' if len(label) > 14 else label
                fontsize = max(6, min(10, int(w * 50)))
                ax.text(x + w / 2, y + h * 0.6, short_label,
                        ha='center', va='center',
                        fontsize=fontsize, color='white',
                        fontweight='bold', clip_on=True)
                if h > 0.1:
                    ax.text(x + w / 2, y + h * 0.3,
                            f'{pct:.1f}%',
                            ha='center', va='center',
                            fontsize=max(5, fontsize - 2), color='white',
                            alpha=0.85, clip_on=True)

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        if title:
            ax.set_title(title, color=_TITLE_CLR, fontsize=10,
                         pad=4, loc='left')

    def _show_no_data(self):
        lbl = QLabel("⏳  Загрузите данные\n(кнопка «📊 Датасеты»)")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"font-size:12px; color:{TEXT_MUT}; background:transparent;")
        self._content_layout.addWidget(lbl)

    def serialize(self) -> dict:
        return dict(self._settings)

    def settings(self) -> dict:
        return dict(self._settings)
