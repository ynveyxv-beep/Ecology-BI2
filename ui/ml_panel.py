# ui/ml_panel.py
"""
Панель классического ML-анализа.
Открывается из ConfiguratorWindow кнопкой «📈 ML».

Вкладки:
  📈 Прогноз   — линейный тренд + прогноз на N шагов
  🔴 Аномалии  — z-score / IQR детекция выбросов
  🔵 Кластеры  — K-Means (numpy, без sklearn)
  🔗 Корреляция — матрица Пирсона + тепловая карта
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QScrollArea, QSizePolicy, QFrame, QGridLayout,
    QRadioButton, QButtonGroup, QMessageBox, QSplitter,
)
import pyqtgraph as pg

import ui.theme as _tm
from ui.theme import register_theme_callback, unregister_theme_callback
from ml.engine import (
    forecast_linear, detect_anomalies, cluster_kmeans, correlate,
    ForecastResult, AnomalyResult, ClusterResult, CorrResult,
)

# ─── Палитра кластеров ────────────────────────────────────────────────────────
_CLUSTER_COLORS = [
    '#38BDF8', '#F87171', '#4ADE80', '#FBBF24',
    '#A78BFA', '#F472B6', '#34D399', '#FB923C',
]


# ─── Worker-поток для ML (чтобы UI не зависал) ───────────────────────────────

class _MLWorker(QThread):
    finished = Signal(object)   # result object
    error    = Signal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            self.finished.emit(self._fn(*self._args, **self._kwargs))
        except Exception as exc:
            self.error.emit(str(exc))


# ─── Вспомогательный виджет: заголовок секции ─────────────────────────────────

class _SectionLabel(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            f"color:{_tm.TEXT_PRI};font-size:12px;font-weight:bold;"
            f"background:transparent;padding:4px 0 2px 0;"
        )


# ─── Утилита: создать plot с нужными стилями ─────────────────────────────────

def _make_plot(title: str = "") -> pg.PlotWidget:
    plot = pg.PlotWidget(title=title)
    plot.setBackground(_tm.BG_DARK)
    plot.showGrid(x=True, y=True, alpha=0.2)
    plot.setMinimumHeight(220)
    _style_plot_axes(plot)
    return plot


def _style_plot_axes(plot: pg.PlotWidget):
    pen_ax  = pg.mkPen(color=_tm.BORDER_LT, width=1)
    pen_txt = pg.mkPen(color=_tm.TEXT_SEC)
    for ax in ('bottom', 'left'):
        a = plot.getAxis(ax)
        a.setPen(pen_ax)
        a.setTextPen(pen_txt)


# ─── Контроль-бар (одинаковый стиль для всех вкладок) ────────────────────────

def _make_combo(parent=None) -> QComboBox:
    c = QComboBox(parent)
    c.setStyleSheet(
        f"QComboBox{{background:{_tm.BG_CARD};color:{_tm.TEXT_PRI};"
        f"border:1px solid {_tm.BORDER};border-radius:5px;padding:4px 8px;"
        f"min-height:26px;}}"
        f"QComboBox:focus{{border-color:{_tm.ACCENT};}}"
        f"QComboBox QAbstractItemView{{background:{_tm.BG_PANEL};"
        f"color:{_tm.TEXT_PRI};selection-background-color:{_tm.BG_ACTIVE};}}"
    )
    return c


def _make_spinbox(parent=None, min_=1, max_=100, val=6) -> QSpinBox:
    s = QSpinBox(parent)
    s.setRange(min_, max_)
    s.setValue(val)
    s.setStyleSheet(
        f"QSpinBox{{background:{_tm.BG_CARD};color:{_tm.TEXT_PRI};"
        f"border:1px solid {_tm.BORDER};border-radius:5px;padding:3px 6px;"
        f"min-height:26px;}}"
        f"QSpinBox:focus{{border-color:{_tm.ACCENT};}}"
    )
    return s


def _make_run_btn(text: str, parent=None) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(
        f"QPushButton{{background:{_tm.ACCENT_DARK};color:{_tm.TEXT_PRI};"
        f"border:none;border-radius:5px;padding:5px 18px;font-weight:bold;}}"
        f"QPushButton:hover{{background:{_tm.ACCENT};color:#0F1A0F;}}"
        f"QPushButton:disabled{{background:{_tm.BORDER};color:{_tm.TEXT_MUT};}}"
    )
    return btn


def _make_metric_card(label: str, value: str) -> QFrame:
    f = QFrame()
    f.setStyleSheet(
        f"QFrame{{background:{_tm.BG_CARD};border:1px solid {_tm.BORDER};"
        f"border-radius:6px;padding:6px 12px;}}"
    )
    lay = QVBoxLayout(f)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(2)
    lbl = QLabel(label)
    lbl.setStyleSheet(f"color:{_tm.TEXT_MUT};font-size:10px;background:transparent;border:none;")
    val = QLabel(value)
    val.setStyleSheet(f"color:{_tm.ACCENT};font-size:14px;font-weight:bold;background:transparent;border:none;")
    val.setObjectName("_val")
    lay.addWidget(lbl)
    lay.addWidget(val)
    return f


# ─── Вкладка 1: Прогноз ───────────────────────────────────────────────────────

class _ForecastTab(QWidget):
    def __init__(self, datasets: dict, parent=None):
        super().__init__(parent)
        self._datasets = datasets
        self._worker   = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # ── Панель управления ──
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        ctrl.addWidget(QLabel("Датасет:"))
        self._ds_combo = _make_combo()
        ctrl.addWidget(self._ds_combo)

        ctrl.addWidget(QLabel("Колонка Y:"))
        self._col_combo = _make_combo()
        ctrl.addWidget(self._col_combo)

        ctrl.addWidget(QLabel("Горизонт:"))
        self._periods = _make_spinbox(min_=1, max_=60, val=6)
        ctrl.addWidget(self._periods)

        self._run_btn = _make_run_btn("▶ Прогноз")
        self._run_btn.clicked.connect(self._run)
        ctrl.addWidget(self._run_btn)
        ctrl.addStretch()
        root.addLayout(ctrl)

        # ── Метрики ──
        m_lay = QHBoxLayout()
        m_lay.setSpacing(8)
        self._card_r2    = _make_metric_card("R²", "—")
        self._card_slope = _make_metric_card("Наклон (за период)", "—")
        self._card_fore  = _make_metric_card("Прогноз (последняя точка)", "—")
        for c in (self._card_r2, self._card_slope, self._card_fore):
            m_lay.addWidget(c)
        m_lay.addStretch()
        root.addLayout(m_lay)

        # ── График ──
        self._plot = _make_plot("Линейный тренд и прогноз")
        root.addWidget(self._plot, 1)

        # ── Статус ──
        self._status = QLabel("")
        self._status.setStyleSheet(f"color:{_tm.TEXT_MUT};font-size:11px;")
        root.addWidget(self._status)

        self._ds_combo.currentIndexChanged.connect(self._on_ds_changed)
        self._populate_ds()

    def _populate_ds(self):
        self._ds_combo.clear()
        for name in self._datasets:
            self._ds_combo.addItem(name, name)
        self._on_ds_changed()

    def _on_ds_changed(self):
        self._col_combo.clear()
        name = self._ds_combo.currentData()
        if not name:
            return
        df = self._datasets.get(name)
        if df is None:
            return
        for col in df.select_dtypes(include='number').columns:
            self._col_combo.addItem(col, col)

    def _run(self):
        ds_name = self._ds_combo.currentData()
        col     = self._col_combo.currentData()
        if not ds_name or not col:
            return
        df = self._datasets.get(ds_name)
        if df is None:
            return

        self._run_btn.setEnabled(False)
        self._status.setText("⏳ Вычисление…")

        self._worker = _MLWorker(forecast_linear, df[col], self._periods.value())
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_done(self, result: ForecastResult):
        self._run_btn.setEnabled(True)
        self._status.setText(
            f"Готово · {len(result.y_hist)} исторических точек · R²={result.r2:.3f}"
        )
        self._update_metrics(result)
        self._draw(result)

    def _on_error(self, msg: str):
        self._run_btn.setEnabled(True)
        self._status.setText(f"⚠️ {msg}")

    def _update_metrics(self, r: ForecastResult):
        def _set_card(card: QFrame, val: str):
            card.findChild(QLabel, "_val").setText(val)

        _set_card(self._card_r2,    f"{r.r2:.4f}")
        _set_card(self._card_slope, f"{r.slope:+.4f}")
        _set_card(self._card_fore,  f"{r.y_fore[-1]:.4f}")

    def _draw(self, r: ForecastResult):
        self._plot.clear()
        # История
        self._plot.plot(r.x_hist, r.y_hist,
                        pen=pg.mkPen(_tm.TEXT_SEC, width=1.5),
                        name="Факт")
        # Тренд
        self._plot.plot(r.x_hist, r.y_trend,
                        pen=pg.mkPen(_tm.ACCENT, width=1.5, style=Qt.DashLine),
                        name="Тренд")
        # Прогноз
        self._plot.plot(r.x_fore, r.y_fore,
                        pen=pg.mkPen('#4ADE80', width=2),
                        name="Прогноз")
        # Доверительный коридор
        x_fill = np.concatenate([r.x_fore, r.x_fore[::-1]])
        y_fill = np.concatenate([r.y_fore_hi, r.y_fore_lo[::-1]])
        fill = pg.PlotDataItem(x_fill, y_fill,
                               pen=pg.mkPen(None),
                               fillLevel=None)
        # Простая граница через две линии
        self._plot.plot(r.x_fore, r.y_fore_hi,
                        pen=pg.mkPen('#4ADE8040', width=1, style=Qt.DotLine))
        self._plot.plot(r.x_fore, r.y_fore_lo,
                        pen=pg.mkPen('#4ADE8040', width=1, style=Qt.DotLine))

    def update_datasets(self, datasets: dict):
        self._datasets = datasets
        self._populate_ds()

    def refresh_theme(self):
        self._plot.setBackground(_tm.BG_DARK)
        _style_plot_axes(self._plot)


# ─── Вкладка 2: Аномалии ─────────────────────────────────────────────────────

class _AnomalyTab(QWidget):
    def __init__(self, datasets: dict, parent=None):
        super().__init__(parent)
        self._datasets = datasets
        self._worker   = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # ── Контроли ──
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        ctrl.addWidget(QLabel("Датасет:"))
        self._ds_combo = _make_combo()
        ctrl.addWidget(self._ds_combo)

        ctrl.addWidget(QLabel("Колонка:"))
        self._col_combo = _make_combo()
        ctrl.addWidget(self._col_combo)

        ctrl.addWidget(QLabel("Метод:"))
        self._method_combo = _make_combo()
        self._method_combo.addItem("Z-score", "zscore")
        self._method_combo.addItem("IQR", "iqr")
        ctrl.addWidget(self._method_combo)

        ctrl.addWidget(QLabel("Порог:"))
        self._thr = QDoubleSpinBox()
        self._thr.setRange(0.1, 10.0)
        self._thr.setSingleStep(0.1)
        self._thr.setValue(2.5)
        self._thr.setDecimals(1)
        self._thr.setStyleSheet(
            f"QDoubleSpinBox{{background:{_tm.BG_CARD};color:{_tm.TEXT_PRI};"
            f"border:1px solid {_tm.BORDER};border-radius:5px;padding:3px 6px;"
            f"min-height:26px;}}"
        )
        ctrl.addWidget(self._thr)

        self._run_btn = _make_run_btn("▶ Найти")
        self._run_btn.clicked.connect(self._run)
        ctrl.addWidget(self._run_btn)
        ctrl.addStretch()
        root.addLayout(ctrl)

        # ── Метрики ──
        m_lay = QHBoxLayout()
        m_lay.setSpacing(8)
        self._card_total  = _make_metric_card("Всего точек", "—")
        self._card_n      = _make_metric_card("Аномалий", "—")
        self._card_pct    = _make_metric_card("Доля, %", "—")
        for c in (self._card_total, self._card_n, self._card_pct):
            m_lay.addWidget(c)
        m_lay.addStretch()
        root.addLayout(m_lay)

        # ── Графики ──
        splitter = QSplitter(Qt.Vertical)
        self._plot_ts  = _make_plot("Временной ряд с аномалиями")
        self._plot_scr = _make_plot("Score аномальности")
        splitter.addWidget(self._plot_ts)
        splitter.addWidget(self._plot_scr)
        splitter.setSizes([300, 160])
        root.addWidget(splitter, 1)

        self._status = QLabel("")
        self._status.setStyleSheet(f"color:{_tm.TEXT_MUT};font-size:11px;")
        root.addWidget(self._status)

        self._ds_combo.currentIndexChanged.connect(self._on_ds_changed)
        self._method_combo.currentIndexChanged.connect(self._on_method_changed)
        self._populate_ds()

    def _populate_ds(self):
        self._ds_combo.clear()
        for name in self._datasets:
            self._ds_combo.addItem(name, name)
        self._on_ds_changed()

    def _on_ds_changed(self):
        self._col_combo.clear()
        name = self._ds_combo.currentData()
        if not name:
            return
        df = self._datasets.get(name)
        if df is None:
            return
        for col in df.select_dtypes(include='number').columns:
            self._col_combo.addItem(col, col)

    def _on_method_changed(self):
        method = self._method_combo.currentData()
        if method == 'zscore':
            self._thr.setValue(2.5)
        else:
            self._thr.setValue(1.5)

    def _run(self):
        ds_name = self._ds_combo.currentData()
        col     = self._col_combo.currentData()
        if not ds_name or not col:
            return
        df = self._datasets.get(ds_name)
        if df is None:
            return

        self._run_btn.setEnabled(False)
        self._status.setText("⏳ Анализ…")

        self._worker = _MLWorker(
            detect_anomalies, df[col],
            method=self._method_combo.currentData(),
            threshold=self._thr.value(),
        )
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_done(self, result: AnomalyResult):
        self._run_btn.setEnabled(True)
        n_total = len(result.y)
        pct = 100.0 * result.n_anomalies / n_total if n_total else 0
        self._status.setText(
            f"Готово · метод={result.method} · порог={result.threshold}"
        )

        def _set(card, val): card.findChild(QLabel, "_val").setText(val)
        _set(self._card_total, str(n_total))
        _set(self._card_n,     str(result.n_anomalies))
        _set(self._card_pct,   f"{pct:.1f}")

        self._draw(result)

    def _on_error(self, msg: str):
        self._run_btn.setEnabled(True)
        self._status.setText(f"⚠️ {msg}")

    def _draw(self, r: AnomalyResult):
        self._plot_ts.clear()
        self._plot_scr.clear()

        # Нормальные точки
        normal = ~r.is_anomaly
        if np.any(normal):
            self._plot_ts.plot(
                r.x[normal], r.y[normal],
                pen=None,
                symbol='o', symbolSize=5,
                symbolBrush=_tm.ACCENT, symbolPen=pg.mkPen(None),
            )
        # Аномалии
        if np.any(r.is_anomaly):
            self._plot_ts.plot(
                r.x[r.is_anomaly], r.y[r.is_anomaly],
                pen=None,
                symbol='x', symbolSize=10,
                symbolBrush=_tm.ACCENT_RED, symbolPen=pg.mkPen(_tm.ACCENT_RED, width=2),
            )
        # Соединяющая линия
        self._plot_ts.plot(r.x, r.y, pen=pg.mkPen(_tm.TEXT_MUT, width=1))

        # Score
        self._plot_scr.plot(
            r.x, r.scores,
            pen=pg.mkPen(_tm.ACCENT_DARK, width=1.5),
        )
        # Порог
        thr_line = pg.InfiniteLine(pos=r.threshold, angle=0,
                                   pen=pg.mkPen(_tm.ACCENT_RED, width=1, style=Qt.DashLine))
        self._plot_scr.addItem(thr_line)

    def update_datasets(self, datasets: dict):
        self._datasets = datasets
        self._populate_ds()

    def refresh_theme(self):
        for p in (self._plot_ts, self._plot_scr):
            p.setBackground(_tm.BG_DARK)
            _style_plot_axes(p)


# ─── Вкладка 3: Кластеры ─────────────────────────────────────────────────────

class _ClusterTab(QWidget):
    def __init__(self, datasets: dict, parent=None):
        super().__init__(parent)
        self._datasets = datasets
        self._worker   = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # ── Контроли ──
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        ctrl.addWidget(QLabel("Датасет:"))
        self._ds_combo = _make_combo()
        ctrl.addWidget(self._ds_combo)

        ctrl.addWidget(QLabel("X:"))
        self._x_combo = _make_combo()
        ctrl.addWidget(self._x_combo)

        ctrl.addWidget(QLabel("Y:"))
        self._y_combo = _make_combo()
        ctrl.addWidget(self._y_combo)

        ctrl.addWidget(QLabel("k:"))
        self._k = _make_spinbox(min_=2, max_=10, val=3)
        ctrl.addWidget(self._k)

        self._run_btn = _make_run_btn("▶ Кластеризовать")
        self._run_btn.clicked.connect(self._run)
        ctrl.addWidget(self._run_btn)
        ctrl.addStretch()
        root.addLayout(ctrl)

        # ── Метрики ──
        m_lay = QHBoxLayout()
        m_lay.setSpacing(8)
        self._card_k        = _make_metric_card("Кластеров", "—")
        self._card_inertia  = _make_metric_card("Инертность", "—")
        self._card_pts      = _make_metric_card("Точек", "—")
        for c in (self._card_k, self._card_inertia, self._card_pts):
            m_lay.addWidget(c)
        m_lay.addStretch()
        root.addLayout(m_lay)

        # ── График ──
        self._plot = _make_plot("Scatter: точки окрашены по кластеру")
        root.addWidget(self._plot, 1)

        self._status = QLabel("")
        self._status.setStyleSheet(f"color:{_tm.TEXT_MUT};font-size:11px;")
        root.addWidget(self._status)

        self._ds_combo.currentIndexChanged.connect(self._on_ds_changed)
        self._populate_ds()

    def _populate_ds(self):
        self._ds_combo.clear()
        for name in self._datasets:
            self._ds_combo.addItem(name, name)
        self._on_ds_changed()

    def _on_ds_changed(self):
        for combo in (self._x_combo, self._y_combo):
            combo.clear()
        name = self._ds_combo.currentData()
        if not name:
            return
        df = self._datasets.get(name)
        if df is None:
            return
        num_cols = list(df.select_dtypes(include='number').columns)
        for col in num_cols:
            self._x_combo.addItem(col, col)
            self._y_combo.addItem(col, col)
        if len(num_cols) > 1:
            self._y_combo.setCurrentIndex(1)

    def _run(self):
        ds_name = self._ds_combo.currentData()
        x_col   = self._x_combo.currentData()
        y_col   = self._y_combo.currentData()
        if not all([ds_name, x_col, y_col]):
            return
        df = self._datasets.get(ds_name)
        if df is None:
            return

        cols = [x_col] if x_col == y_col else [x_col, y_col]

        self._run_btn.setEnabled(False)
        self._status.setText("⏳ Кластеризация…")

        self._worker = _MLWorker(cluster_kmeans, df, cols, self._k.value())
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_done(self, result: ClusterResult):
        self._run_btn.setEnabled(True)
        self._status.setText(
            f"Готово · {result.k} кластеров · {len(result.labels)} точек"
        )

        def _set(card, val): card.findChild(QLabel, "_val").setText(val)
        _set(self._card_k,       str(result.k))
        _set(self._card_inertia, f"{result.inertia:.2f}")
        _set(self._card_pts,     str(len(result.labels)))

        self._draw(result)

    def _on_error(self, msg: str):
        self._run_btn.setEnabled(True)
        self._status.setText(f"⚠️ {msg}")

    def _draw(self, r: ClusterResult):
        self._plot.clear()
        for k in range(r.k):
            mask = r.labels == k
            color = _CLUSTER_COLORS[k % len(_CLUSTER_COLORS)]
            self._plot.plot(
                r.x[mask], r.y[mask],
                pen=None,
                symbol='o', symbolSize=7,
                symbolBrush=pg.mkBrush(color),
                symbolPen=pg.mkPen(None),
                name=f"Кластер {k + 1}",
            )
        # Центроиды
        cx = r.centroids[:, 0]
        cy = r.centroids[:, 1] if r.centroids.shape[1] > 1 else np.zeros(r.k)
        self._plot.plot(
            cx, cy,
            pen=None,
            symbol='star', symbolSize=16,
            symbolBrush=pg.mkBrush('#FFFFFF'),
            symbolPen=pg.mkPen('#000000', width=1),
        )

    def update_datasets(self, datasets: dict):
        self._datasets = datasets
        self._populate_ds()

    def refresh_theme(self):
        self._plot.setBackground(_tm.BG_DARK)
        _style_plot_axes(self._plot)


# ─── Вкладка 4: Корреляция ───────────────────────────────────────────────────

class _CorrTab(QWidget):
    def __init__(self, datasets: dict, parent=None):
        super().__init__(parent)
        self._datasets = datasets
        self._worker   = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # ── Контроли ──
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)
        ctrl.addWidget(QLabel("Датасет:"))
        self._ds_combo = _make_combo()
        ctrl.addWidget(self._ds_combo)

        self._run_btn = _make_run_btn("▶ Корреляция")
        self._run_btn.clicked.connect(self._run)
        ctrl.addWidget(self._run_btn)
        ctrl.addStretch()
        root.addLayout(ctrl)

        # ── Топ пар ──
        self._top_label = QLabel("Топ-5 коррелирующих пар")
        self._top_label.setStyleSheet(
            f"color:{_tm.TEXT_SEC};font-size:11px;background:transparent;"
        )
        root.addWidget(self._top_label)

        # ── График: тепловая карта через ImageItem ──
        self._plot = pg.PlotWidget()
        self._plot.setBackground(_tm.BG_DARK)
        self._plot.setMinimumHeight(280)
        self._plot.setAspectLocked(True)
        root.addWidget(self._plot, 1)

        # ── Легенда-шкала (colorbar текст) ──
        self._cbar_label = QLabel("")
        self._cbar_label.setStyleSheet(
            f"color:{_tm.TEXT_MUT};font-size:10px;background:transparent;"
        )
        root.addWidget(self._cbar_label)

        self._status = QLabel("")
        self._status.setStyleSheet(f"color:{_tm.TEXT_MUT};font-size:11px;")
        root.addWidget(self._status)

        self._ds_combo.currentIndexChanged.connect(self._on_ds_changed)
        self._populate_ds()

    def _populate_ds(self):
        self._ds_combo.clear()
        for name in self._datasets:
            self._ds_combo.addItem(name, name)

    def _on_ds_changed(self):
        pass

    def _run(self):
        ds_name = self._ds_combo.currentData()
        if not ds_name:
            return
        df = self._datasets.get(ds_name)
        if df is None:
            return

        self._run_btn.setEnabled(False)
        self._status.setText("⏳ Вычисление корреляции…")

        self._worker = _MLWorker(correlate, df)
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_done(self, result: CorrResult):
        self._run_btn.setEnabled(True)
        n = len(result.columns)
        self._status.setText(f"Готово · {n} переменных · матрица {n}×{n}")

        # Топ пар
        lines = []
        for a, b, v in result.top_pairs:
            bar = "█" * int(abs(v) * 10) + "░" * (10 - int(abs(v) * 10))
            sign = "+" if v >= 0 else "−"
            lines.append(f"  {sign}{abs(v):.3f}  {bar}  {a} ↔ {b}")
        self._top_label.setText("Топ-5 пар по |r|:\n" + "\n".join(lines))

        self._draw_heatmap(result)

    def _on_error(self, msg: str):
        self._run_btn.setEnabled(True)
        self._status.setText(f"⚠️ {msg}")

    def _draw_heatmap(self, result: CorrResult):
        self._plot.clear()
        cols = result.columns
        n = len(cols)
        mat = result.matrix.to_numpy(dtype=float)

        # Нормализация в [0, 255] (−1 → 0, 0 → 127, +1 → 255)
        mat_norm = ((mat + 1) / 2 * 255).astype(np.uint8)

        # Цветовая карта: синий (−1) → серый (0) → зелёный (+1)
        cmap_r = np.array([int(_tm.ACCENT_RED[1:3],   16)] * 128 +
                           list(range(int(_tm.ACCENT_RED[1:3],   16),
                                      int(_tm.ACCENT[1:3], 16)+1,
                                      max(1,(int(_tm.ACCENT[1:3], 16)-
                                             int(_tm.ACCENT_RED[1:3], 16))//128)))[:128])

        # Простая RGB-матрица через pg.ImageItem
        # Colour: -1=red, 0=dark, +1=accent
        def _lerp_color(t, c1_hex, c2_hex):
            """t in [0,1], returns (r,g,b)"""
            def h(x): return int(x, 16)
            r1,g1,b1 = h(c1_hex[1:3]),h(c1_hex[3:5]),h(c1_hex[5:7])
            r2,g2,b2 = h(c2_hex[1:3]),h(c2_hex[3:5]),h(c2_hex[5:7])
            return (int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t))

        rgb = np.zeros((n, n, 3), dtype=np.uint8)
        for i in range(n):
            for j in range(n):
                v = mat[i, j]
                if np.isnan(v):
                    rgb[i, j] = (60, 60, 60)
                elif v < 0:
                    rgb[i, j] = _lerp_color(v + 1,
                                             _tm.ACCENT_RED,
                                             _tm.BG_CARD)
                else:
                    rgb[i, j] = _lerp_color(v,
                                             _tm.BG_CARD,
                                             _tm.ACCENT)

        img = pg.ImageItem(rgb)
        # Flip Y so row 0 is at top
        img.setTransform(pg.QtGui.QTransform().scale(1, -1).translate(0, -n))
        self._plot.addItem(img)

        # Подписи осей
        ax_b = self._plot.getAxis('bottom')
        ax_l = self._plot.getAxis('left')
        ticks = [(i + 0.5, c) for i, c in enumerate(cols)]
        ticks_inv = [(n - i - 0.5, c) for i, c in enumerate(cols)]
        ax_b.setTicks([ticks])
        ax_l.setTicks([ticks_inv])
        ax_b.setPen(pg.mkPen(_tm.BORDER_LT))
        ax_b.setTextPen(pg.mkPen(_tm.TEXT_SEC))
        ax_l.setPen(pg.mkPen(_tm.BORDER_LT))
        ax_l.setTextPen(pg.mkPen(_tm.TEXT_SEC))

        self._cbar_label.setText(
            "Шкала: красный = −1 (обратная корреляция)  ·  "
            "тёмный = 0 (нет связи)  ·  "
            f"{_tm.ACCENT} = +1 (прямая корреляция)"
        )

    def update_datasets(self, datasets: dict):
        self._datasets = datasets
        self._populate_ds()

    def refresh_theme(self):
        self._plot.setBackground(_tm.BG_DARK)
        _style_plot_axes(self._plot)


# ─── Главный диалог ──────────────────────────────────────────────────────────

class MLPanel(QDialog):
    """
    Модальный (но не блокирующий) диалог ML-анализа.
    Используйте show() (не exec_()) чтобы оставить основное окно доступным.
    """

    def __init__(self, datasets: dict, parent=None):
        super().__init__(parent)
        self._datasets = datasets
        self.setWindowTitle("📈 ML-анализ")
        self.resize(860, 620)
        self.setMinimumSize(680, 480)
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        self._build()
        self._apply_theme()
        register_theme_callback(self.refresh_theme)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Заголовок ──
        header = QWidget()
        header.setFixedHeight(44)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 0, 16, 0)
        icon = QLabel("📈")
        icon.setStyleSheet("font-size:18px;background:transparent;border:none;")
        h_lay.addWidget(icon)
        title = QLabel("ML-анализ данных")
        title.setStyleSheet(
            f"color:{_tm.TEXT_PRI};font-size:14px;font-weight:bold;"
            f"background:transparent;border:none;"
        )
        h_lay.addWidget(title, 1)
        self._header = header
        root.addWidget(header)

        # ── Вкладки ──
        self._tabs = QTabWidget()
        self._tab_forecast = _ForecastTab(self._datasets)
        self._tab_anomaly  = _AnomalyTab(self._datasets)
        self._tab_cluster  = _ClusterTab(self._datasets)
        self._tab_corr     = _CorrTab(self._datasets)

        self._tabs.addTab(self._tab_forecast, "📈 Прогноз")
        self._tabs.addTab(self._tab_anomaly,  "🔴 Аномалии")
        self._tabs.addTab(self._tab_cluster,  "🔵 Кластеры")
        self._tabs.addTab(self._tab_corr,     "🔗 Корреляция")
        root.addWidget(self._tabs, 1)

    def _apply_theme(self):
        self.setStyleSheet(
            f"QDialog{{background:{_tm.BG_DARK};color:{_tm.TEXT_PRI};}}"
        )
        self._header.setStyleSheet(
            f"background:{_tm.BG_DEEP};border-bottom:1px solid {_tm.BORDER};"
        )
        self._tabs.setStyleSheet(
            f"QTabWidget::pane{{border:none;background:{_tm.BG_DARK};}}"
            f"QTabBar::tab{{padding:8px 18px;background:{_tm.BG_CARD};"
            f"border:none;color:{_tm.TEXT_SEC};font-size:12px;}}"
            f"QTabBar::tab:selected{{background:{_tm.BG_PANEL};"
            f"font-weight:bold;color:{_tm.TEXT_PRI};}}"
            f"QTabBar::tab:hover{{background:{_tm.BG_HOVER};color:{_tm.TEXT_PRI};}}"
        )
        # QLabel внутри tabs
        label_style = (
            f"QLabel{{color:{_tm.TEXT_PRI};background:transparent;}}"
        )
        self.setStyleSheet(
            self.styleSheet() + label_style
        )

    def refresh_theme(self):
        self._apply_theme()
        for tab in (self._tab_forecast, self._tab_anomaly,
                    self._tab_cluster, self._tab_corr):
            tab.refresh_theme()

    def set_datasets(self, datasets: dict):
        self._datasets = datasets
        for tab in (self._tab_forecast, self._tab_anomaly,
                    self._tab_cluster, self._tab_corr):
            tab.update_datasets(datasets)

    def closeEvent(self, event):
        unregister_theme_callback(self.refresh_theme)
        super().closeEvent(event)
