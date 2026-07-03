# ui/eco_dashboard_window.py - ПОЛНАЯ ВЕРСИЯ С НАСТРОЙКАМИ + ПОДДЕРЖКА ТЕМ
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QGridLayout, QComboBox, QProgressBar
)

import pandas as pd
import numpy as np
import pyqtgraph as pg
import traceback
import os
from datetime import datetime

from logger import logger, LoggerMixin
from ui.chart_settings_dialog import ChartSettingsDialog
import ui.theme as _tm
from ui.theme import THEME_LIST, register_theme_callback, unregister_theme_callback


class EcoDashboardWindow(QWidget, LoggerMixin):
    """Экологический дашборд - ПОЛНАЯ ВЕРСИЯ С НАСТРОЙКАМИ + ТЕМЫ"""

    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.log.info("🚀 Инициализация EcoDashboardWindow")

        self.data = None
        self.filtered_data = None
        self._is_building = False
        self.chart_settings = {}
        self._current_plots = {}
        self._ts_all_data = {}
        self._ts_active_days = 0

        self.init_ui()
        self.show_welcome()

        # Подписываемся на смену темы и сразу применяем текущую
        register_theme_callback(self.refresh_theme)
        self.refresh_theme()

        self.log.info("✅ EcoDashboardWindow инициализирован")

    def closeEvent(self, event):
        """При закрытии снимаем колбэк, чтобы не было утечки."""
        unregister_theme_callback(self.refresh_theme)
        super().closeEvent(event)

    # ─── ТЕМА ─────────────────────────────────────────────────────────────────

    def refresh_theme(self) -> None:
        """Применяет текущую тему ко всем виджетам окна."""
        tm = _tm  # удобный алиас

        # ── Общий override для дочерних виджетов ──────────────────────────────
        # Этот setStyleSheet перекрывает app.setStyleSheet() для данного окна
        self.setStyleSheet(f"""
            QWidget             {{ background: {tm.BG_DARK}; color: {tm.TEXT_PRI}; }}
            QLabel              {{ color: {tm.TEXT_PRI}; background: transparent; }}
            QTableWidget        {{ background: {tm.BG_CARD}; color: {tm.TEXT_PRI};
                                   gridline-color: {tm.BORDER}; border: 1px solid {tm.BORDER};
                                   border-radius: 4px; }}
            QTableWidget::item  {{ background: {tm.BG_CARD}; color: {tm.TEXT_PRI}; padding: 2px 4px; }}
            QTableWidget::item:selected {{ background: {tm.BG_ACTIVE}; color: {tm.ACCENT}; }}
            QHeaderView::section {{ background: {tm.BG_PANEL}; color: {tm.TEXT_SEC};
                                    border: 1px solid {tm.BORDER}; padding: 4px 6px; }}
            QTabWidget::pane    {{ border: none; background: {tm.BG_DARK}; }}
            QTabBar::tab        {{ padding: 8px 16px; background: {tm.BG_CARD};
                                   border: none; color: {tm.TEXT_SEC}; }}
            QTabBar::tab:selected {{ background: {tm.BG_PANEL}; font-weight: bold;
                                     color: {tm.TEXT_PRI}; }}
            QTabBar::tab:hover  {{ background: {tm.BG_HOVER}; color: {tm.TEXT_PRI}; }}
            QComboBox           {{ background: {tm.BG_CARD}; color: {tm.TEXT_PRI};
                                   border: 1px solid {tm.BORDER}; border-radius: 4px;
                                   padding: 4px 8px; min-height: 26px; }}
            QComboBox:hover     {{ border-color: {tm.BORDER_LT}; }}
            QComboBox::drop-down {{ border: none; width: 18px; }}
            QComboBox QAbstractItemView {{ background: {tm.BG_PANEL}; color: {tm.TEXT_PRI};
                                           border: 1px solid {tm.BORDER_LT};
                                           selection-background-color: {tm.BG_ACTIVE};
                                           selection-color: {tm.ACCENT}; }}
            QPushButton         {{ background: {tm.BG_CARD}; color: {tm.TEXT_SEC};
                                   border: 1px solid {tm.BORDER}; border-radius: 4px;
                                   padding: 4px 12px; }}
            QPushButton:hover   {{ background: {tm.BG_HOVER}; border-color: {tm.BORDER_LT};
                                   color: {tm.TEXT_PRI}; }}
            QPushButton:pressed {{ background: {tm.BG_ACTIVE}; }}
            QPushButton:disabled {{ color: {tm.TEXT_MUT}; }}
            QScrollBar:vertical   {{ background: {tm.BG_DARK}; width: 6px; margin: 0; }}
            QScrollBar::handle:vertical {{ background: {tm.BORDER}; border-radius: 3px; min-height: 24px; }}
            QScrollBar::handle:vertical:hover {{ background: {tm.BORDER_LT}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar:horizontal {{ background: {tm.BG_DARK}; height: 6px; margin: 0; }}
            QScrollBar::handle:horizontal {{ background: {tm.BORDER}; border-radius: 3px; min-width: 24px; }}
            QScrollBar::handle:horizontal:hover {{ background: {tm.BORDER_LT}; }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
        """)

        # ── Тулбар ────────────────────────────────────────────────────────────
        self._toolbar.setStyleSheet(
            f"background: {tm.BG_PANEL}; border-bottom: 1px solid {tm.BORDER};"
        )
        self.info_label.setStyleSheet(f"color: {tm.TEXT_MUT}; font-size: 12px;")

        # ── Синхронизируем комбо тем (без рекурсии) ───────────────────────────
        self._theme_combo.blockSignals(True)
        for i in range(self._theme_combo.count()):
            if self._theme_combo.itemData(i) == tm.CURRENT_THEME_NAME:
                self._theme_combo.setCurrentIndex(i)
                break
        self._theme_combo.blockSignals(False)

        # ── Вкладки (widget-level стиль перекрывает родительский) ────────────
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background: {tm.BG_DARK}; }}
            QTabBar::tab {{
                padding: 8px 16px; background: {tm.BG_CARD};
                border: none; color: {tm.TEXT_SEC};
            }}
            QTabBar::tab:selected {{
                background: {tm.BG_PANEL}; font-weight: bold; color: {tm.TEXT_PRI};
            }}
            QTabBar::tab:hover {{
                background: {tm.BG_HOVER}; color: {tm.TEXT_PRI};
            }}
        """)

        # ── Прогресс-бар ──────────────────────────────────────────────────────
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {tm.BORDER}; border: none; border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background: {tm.ACCENT}; border-radius: 2px;
            }}
        """)

        # ── Кнопки периодов ───────────────────────────────────────────────────
        for btn, _ in self._period_buttons:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {tm.BG_CARD}; border: 1px solid {tm.BORDER};
                    border-radius: 4px; font-size: 11px; padding: 0 8px;
                    color: {tm.TEXT_SEC};
                }}
                QPushButton:hover   {{ background: {tm.BG_HOVER}; color: {tm.TEXT_PRI}; }}
                QPushButton:checked {{ background: {tm.ACCENT_DARK}; color: white;
                                       border-color: {tm.ACCENT}; }}
            """)

        # ── pyqtgraph графики ─────────────────────────────────────────────────
        axis_pen  = pg.mkPen(color=tm.BORDER_LT, width=1)
        text_pen  = pg.mkPen(color=tm.TEXT_SEC)
        for plot in (self.ts_plot, self.plot, self.cat_plot,
                     self.geo_plot, self.trash_plot):
            plot.setBackground(tm.BG_DARK)
            for axis_name in ('bottom', 'left'):
                ax = plot.getAxis(axis_name)
                ax.setPen(axis_pen)
                ax.setTextPen(text_pen)

    def _on_eco_theme_changed(self, index: int) -> None:
        """Применяет выбранную тему из комбо статического дашборда."""
        theme_id = self._theme_combo.itemData(index)
        if theme_id:
            _tm.set_active_theme(theme_id)

    # ─── ИНИЦИАЛИЗАЦИЯ UI ──────────────────────────────────────────────────────

    def init_ui(self):
        """Инициализация интерфейса"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ─── Верхняя панель ─────────────────────────────────────────────────
        toolbar = QWidget()
        self._toolbar = toolbar   # сохраняем для refresh_theme()
        toolbar.setStyleSheet("background: #f8f9fa; border-bottom: 1px solid #dee2e6;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)

        back_btn = QPushButton("← Назад")
        back_btn.clicked.connect(self.go_back)
        toolbar_layout.addWidget(back_btn)

        toolbar_layout.addWidget(QLabel("|"))

        self.load_btn = QPushButton("📂 Загрузить данные")
        self.load_btn.clicked.connect(self.load_data)
        toolbar_layout.addWidget(self.load_btn)

        self.report_btn = QPushButton("📊 Экспорт отчёта")
        self.report_btn.clicked.connect(self.export_report)
        self.report_btn.setEnabled(False)
        toolbar_layout.addWidget(self.report_btn)

        toolbar_layout.addStretch()

        # ── Выбор темы ──────────────────────────────────────────────────────
        theme_lbl = QLabel("🎨")
        theme_lbl.setStyleSheet("background: transparent; font-size: 13px;")
        toolbar_layout.addWidget(theme_lbl)

        self._theme_combo = QComboBox()
        self._theme_combo.setFixedWidth(130)
        for theme_id, theme_name in THEME_LIST:
            self._theme_combo.addItem(theme_name, theme_id)
        self._theme_combo.currentIndexChanged.connect(self._on_eco_theme_changed)
        toolbar_layout.addWidget(self._theme_combo)

        toolbar_layout.addSpacing(8)

        self.info_label = QLabel("Данные не загружены")
        self.info_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        toolbar_layout.addWidget(self.info_label)

        main_layout.addWidget(toolbar)

        # ─── Прогресс-бар (скрыт по умолчанию) ─────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #dee2e6;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background: #1F4E79;
                border-radius: 2px;
            }
        """)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # ─── Вкладки ──────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: #f5f5f5; }
            QTabBar::tab { padding: 8px 16px; background: #e9ecef; border: none; }
            QTabBar::tab:selected { background: white; font-weight: bold; }
        """)

        self.tab_overview = QWidget()
        self.tab_categories = QWidget()
        self.tab_geography = QWidget()
        self.tab_trash = QWidget()

        self.tabs.addTab(self.tab_overview, "📊 Обзор")
        self.tabs.addTab(self.tab_categories, "📋 Категории")
        self.tabs.addTab(self.tab_geography, "🗺️ География")
        self.tabs.addTab(self.tab_trash, "♻️ Мусор")

        main_layout.addWidget(self.tabs)

        self._create_overview_widgets()
        self._create_categories_widgets()
        self._create_geography_widgets()
        self._create_trash_widgets()

    # ─── ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ──────────────────────────────────────────

    def _create_plot_container(self, plot_widget, title: str, settings_key: str):
        """Создаёт контейнер с графиком и кнопкой настроек"""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(2)

        header = QHBoxLayout()
        header.setContentsMargins(5, 0, 5, 0)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        header.addWidget(title_label)
        header.addStretch()

        settings_btn = QPushButton("⋮")
        settings_btn.setFixedSize(30, 25)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 18px;
                font-weight: bold;
                color: #6c757d;
            }
            QPushButton:hover {
                color: #1F4E79;
                background-color: #e9ecef;
                border-radius: 4px;
            }
        """)
        settings_btn.clicked.connect(lambda: self._open_chart_settings(plot_widget, settings_key))
        header.addWidget(settings_btn)

        container_layout.addLayout(header)
        container_layout.addWidget(plot_widget)

        plot_widget.setMouseEnabled(x=False, y=False)

        return container

    def _open_chart_settings(self, plot_widget, settings_key: str):
        """Открывает диалог настроек графика"""
        current = self.chart_settings.get(settings_key, {})
        dialog = ChartSettingsDialog(current, self)
        dialog.settings_applied.connect(
            lambda settings: self._apply_chart_settings(plot_widget, settings_key, settings)
        )
        dialog.exec()

    def _apply_chart_settings(self, plot_widget, settings_key: str, settings: dict):
        """Применяет настройки к графику"""
        self.chart_settings[settings_key] = settings

        try:
            if settings.get('scale_mode') == 'Ручной':
                try:
                    plot_widget.setXRange(settings.get('min_x', 0), settings.get('max_x', 100))
                    plot_widget.setYRange(settings.get('min_y', 0), settings.get('max_y', 100))
                except:
                    plot_widget.autoRange()
            else:
                plot_widget.autoRange()

            bg_color = settings.get('bg_color', None)
            if bg_color:
                plot_widget.setBackground(bg_color)

            enable_pan = settings.get('enable_pan', False)
            plot_widget.setMouseEnabled(x=enable_pan, y=enable_pan)

            if not settings.get('enable_zoom', False):
                plot_widget.setMouseEnabled(x=False, y=False)

            x_label = settings.get('x_label', '')
            y_label = settings.get('y_label', '')
            if x_label:
                plot_widget.setLabel('bottom', x_label)
            if y_label:
                plot_widget.setLabel('left', y_label)

            title = settings.get('title', '')
            if title:
                plot_widget.setTitle(title)

            if hasattr(plot_widget, 'legend') and plot_widget.legend:
                plot_widget.legend.setVisible(settings.get('show_legend', True))

            font_size = settings.get('font_size', 10)
            from PySide6.QtGui import QFont
            plot_widget.getAxis('bottom').setTickFont(QFont("Arial", font_size))
            plot_widget.getAxis('left').setTickFont(QFont("Arial", font_size))

            if hasattr(self, '_current_df') and self._current_df is not None:
                self._rebuild_plot_with_settings(plot_widget, settings_key, settings)

            plot_widget.repaint()

        except Exception as e:
            self.log.warning(f"⚠️ Ошибка применения настроек: {e}")

    def _apply_aggregation(self, df, settings: dict):
        """Применяет агрегацию к данным"""
        if df is None or len(df) == 0:
            return df

        aggregation = settings.get('aggregation', 'Без агрегации')
        if aggregation == 'Без агрегации':
            return df

        if 'date' not in df.columns:
            return df

        df_copy = df.copy()
        df_copy['date'] = pd.to_datetime(df_copy['date'], errors='coerce')
        df_copy = df_copy.dropna(subset=['date'])

        if len(df_copy) == 0:
            return df

        freq_map = {
            'По дням': 'D',
            'По неделям': 'W',
            'По месяцам': 'M',
            'По кварталам': 'Q',
            'По годам': 'Y'
        }
        freq = freq_map.get(aggregation, 'D')

        df_copy['period'] = df_copy['date'].dt.to_period(freq)

        agg_method = settings.get('agg_method', 'Сумма')
        agg_func_map = {
            'Сумма': 'sum',
            'Среднее': 'mean',
            'Максимум': 'max',
            'Минимум': 'min',
            'Количество': 'count'
        }
        agg_func = agg_func_map.get(agg_method, 'sum')

        grouped = df_copy.groupby('period')

        if agg_method == 'Количество':
            result = grouped.size().reset_index(name='count')
        else:
            numeric_cols = df_copy.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                result = grouped.size().reset_index(name='count')
            else:
                result = grouped[numeric_cols[0]].agg(agg_func).reset_index()
                result.columns = ['period', 'value']

        result['date'] = result['period'].dt.start_time

        return result

    def _apply_sorting(self, df, settings: dict):
        """Применяет сортировку к данным"""
        if df is None or len(df) == 0:
            return df

        sort_by = settings.get('sort_by', 'По дате')
        sort_order = settings.get('sort_order', 'По возрастанию')
        limit = settings.get('limit', 0)
        reverse = settings.get('reverse_order', False)

        ascending = sort_order == 'По возрастанию'

        sort_col_map = {
            'По дате': 'date' if 'date' in df.columns else None,
            'По значению': 'value' if 'value' in df.columns else None,
            'По категории': 'category' if 'category' in df.columns else None
        }
        sort_col = sort_col_map.get(sort_by)

        if sort_col and sort_col in df.columns:
            df = df.sort_values(by=sort_col, ascending=ascending)

        if reverse:
            df = df.iloc[::-1].reset_index(drop=True)

        if limit > 0 and len(df) > limit:
            df = df.head(limit)

        return df

    def _rebuild_plot_with_settings(self, plot_widget, settings_key: str, settings: dict):
        """Перестраивает график с учётом настроек агрегации и сортировки"""
        pass

    # ─── ВКЛАДКА "ОБЗОР" ──────────────────────────────────────────────────

    def _create_overview_widgets(self):
        """Создаёт виджеты для вкладки Обзор"""
        layout = QVBoxLayout(self.tab_overview)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        self.kpi_container = QWidget()
        self.kpi_layout = QGridLayout(self.kpi_container)
        self.kpi_layout.setSpacing(10)
        layout.addWidget(self.kpi_container)

        self.kpi_cards = []
        kpi_labels = ["Всего", "Выполнено", "В работе", "% выполнения", "ОМСУ", "Период"]
        kpi_colors = ["#1F4E79", "#28a745", "#fd7e14", "#17a2b8", "#6c757d", "#343a40"]

        for i, (label, color) in enumerate(zip(kpi_labels, kpi_colors)):
            card = QWidget()
            card.setFixedHeight(75)
            card.setMinimumWidth(100)
            card.setStyleSheet(f"""
                background-color: {color};
                border-radius: 8px;
                padding: 5px;
            """)

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 5, 10, 5)

            value_label = QLabel("—")
            value_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
            value_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(value_label)

            name_label = QLabel(label)
            name_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 11px;")
            name_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(name_label)

            self.kpi_layout.addWidget(card, i // 3, i % 3)
            self.kpi_cards.append((value_label, name_label))

        date_axis = pg.DateAxisItem(orientation='bottom')
        self.ts_plot = pg.PlotWidget(axisItems={'bottom': date_axis})
        self.ts_plot.setBackground('white')
        self.ts_plot.setMinimumHeight(250)
        self.ts_plot.setLabel('left', 'Количество')
        self.ts_plot.setLabel('bottom', 'Дата')
        self.ts_plot.addLegend()
        self._ts_all_data = {}

        ts_outer = QWidget()
        ts_outer_layout = QVBoxLayout(ts_outer)
        ts_outer_layout.setContentsMargins(0, 0, 0, 0)
        ts_outer_layout.setSpacing(4)

        period_row = QWidget()
        period_row_layout = QHBoxLayout(period_row)
        period_row_layout.setContentsMargins(5, 0, 5, 0)
        period_row_layout.setSpacing(4)

        period_label = QLabel("📅 Период:")
        period_label.setStyleSheet("font-size:11px; color:#6c757d;")
        period_row_layout.addWidget(period_label)

        self._period_buttons = []
        for label, days in [("7д", 7), ("30д", 30), ("90д", 90), ("1г", 365), ("Всё", 0)]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(22)
            btn.setStyleSheet("""
                QPushButton {
                    background: #e9ecef; border: 1px solid #dee2e6;
                    border-radius: 4px; font-size: 11px; padding: 0 8px; color: #495057;
                }
                QPushButton:hover { background: #dee2e6; }
                QPushButton:checked { background: #1F4E79; color: white; border-color: #1F4E79; }
            """)
            btn.clicked.connect(lambda checked, d=days: self._ts_set_period(d))
            period_row_layout.addWidget(btn)
            self._period_buttons.append((btn, days))

        self._period_buttons[-1][0].setChecked(True)
        self._ts_active_days = 0

        period_row_layout.addStretch()
        ts_outer_layout.addWidget(period_row)

        ts_container = self._create_plot_container(
            self.ts_plot,
            "📈 Динамика обращений",
            "time_series"
        )
        ts_outer_layout.addWidget(ts_container)
        layout.addWidget(ts_outer)

        self.plot = pg.PlotWidget()
        self.plot.setBackground('white')
        self.plot.setMinimumHeight(250)
        self.plot.setLabel('left', 'Количество')
        self.plot.setLabel('bottom', 'Категория')

        cat_container = self._create_plot_container(
            self.plot,
            "🏆 Топ категорий",
            "top_categories"
        )
        layout.addWidget(cat_container)

    # ─── ВКЛАДКА "КАТЕГОРИИ" ─────────────────────────────────────────────

    def _create_categories_widgets(self):
        """Создаёт виджеты для вкладки Категории"""
        layout = QVBoxLayout(self.tab_categories)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        self.cat_table = QTableWidget()
        self.cat_table.setColumnCount(5)
        self.cat_table.setHorizontalHeaderLabels(["Категория", "Всего", "Доля %", "Выполнено", "В работе"])
        self.cat_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.cat_table)

        self.cat_plot = pg.PlotWidget()
        self.cat_plot.setBackground('white')
        self.cat_plot.setMinimumHeight(250)
        self.cat_plot.setLabel('left', 'Количество')
        self.cat_plot.setLabel('bottom', 'Категория')

        cat_plot_container = self._create_plot_container(
            self.cat_plot,
            "📊 Распределение по категориям",
            "categories_chart"
        )
        layout.addWidget(cat_plot_container)

    # ─── ВКЛАДКА "ГЕОГРАФИЯ" ──────────────────────────────────────────────

    def _create_geography_widgets(self):
        """Создаёт виджеты для вкладки География"""
        layout = QVBoxLayout(self.tab_geography)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        geo_switch = QHBoxLayout()
        geo_switch.addWidget(QLabel("Показать:"))
        self.geo_type = QComboBox()
        self.geo_type.addItems(["По ОМСУ", "По МРО"])
        self.geo_type.currentTextChanged.connect(self.update_geography)
        geo_switch.addWidget(self.geo_type)
        geo_switch.addStretch()
        layout.addLayout(geo_switch)

        self.geo_table = QTableWidget()
        self.geo_table.setColumnCount(6)
        self.geo_table.setHorizontalHeaderLabels(["Наименование", "Всего", "Доля %", "Выполнено", "В работе", "Бэклог %"])
        self.geo_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.geo_table)

        self.geo_plot = pg.PlotWidget()
        self.geo_plot.setBackground('white')
        self.geo_plot.setMinimumHeight(250)
        self.geo_plot.setLabel('left', 'Количество')
        self.geo_plot.setLabel('bottom', 'Наименование')

        geo_plot_container = self._create_plot_container(
            self.geo_plot,
            "🗺️ Распределение по территории",
            "geography_chart"
        )
        layout.addWidget(geo_plot_container)

    # ─── ВКЛАДКА "МУСОР" ──────────────────────────────────────────────────

    def _create_trash_widgets(self):
        """Создаёт виджеты для вкладки Мусор"""
        layout = QVBoxLayout(self.tab_trash)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        self.trash_info = QLabel("♻️ Аналитика 'Мусор, свалки, стоки'")
        self.trash_info.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.trash_info)

        trash_row = QHBoxLayout()
        trash_row.setSpacing(15)

        left_col = QVBoxLayout()
        left_col.addWidget(QLabel("🏆 Топ по числу обращений"))
        self.trash_count_table = QTableWidget()
        self.trash_count_table.setColumnCount(6)
        self.trash_count_table.setHorizontalHeaderLabels(["ОМСУ", "Всего", "Доля %", "Выполнено", "В работе", "Бэклог %"])
        self.trash_count_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        left_col.addWidget(self.trash_count_table)
        trash_row.addLayout(left_col, 1)

        right_col = QVBoxLayout()
        right_col.addWidget(QLabel("🏆 Топ по бэклогу"))
        self.trash_backlog_table = QTableWidget()
        self.trash_backlog_table.setColumnCount(6)
        self.trash_backlog_table.setHorizontalHeaderLabels(["ОМСУ", "Всего", "Доля %", "Выполнено", "В работе", "Бэклог %"])
        self.trash_backlog_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_col.addWidget(self.trash_backlog_table)
        trash_row.addLayout(right_col, 1)

        layout.addLayout(trash_row)

        self.trash_plot = pg.PlotWidget()
        self.trash_plot.setBackground('white')
        self.trash_plot.setMinimumHeight(200)
        self.trash_plot.setLabel('left', 'Количество')
        self.trash_plot.setLabel('bottom', 'ОМСУ')

        trash_plot_container = self._create_plot_container(
            self.trash_plot,
            "♻️ Мусор, свалки, стоки",
            "trash_chart"
        )
        layout.addWidget(trash_plot_container)

    # ─── ПРИВЕТСТВИЕ ──────────────────────────────────────────────────────

    def show_welcome(self):
        """Показывает приветствие"""
        for value_label, name_label in self.kpi_cards:
            value_label.setText("—")

        for plot in [self.ts_plot, self.plot, self.cat_plot, self.geo_plot, self.trash_plot]:
            plot.clear()
            text = pg.TextItem("🌿 Загрузите данные", color=(150, 150, 150))
            text.setPos(0, 0)
            plot.addItem(text)

        for table in [self.cat_table, self.geo_table, self.trash_count_table, self.trash_backlog_table]:
            table.setRowCount(0)

        self.info_label.setText("Данные не загружены")
        self.report_btn.setEnabled(False)

    # ─── ЗАГРУЗКА ДАННЫХ ──────────────────────────────────────────────────

    def load_data(self):
        """Загружает данные через диалог"""
        self.log.info("📂 Начало загрузки данных")

        try:
            path, _ = QFileDialog.getOpenFileName(
                self, "Загрузить данные", "", "Excel (*.xlsx *.xls);;CSV (*.csv)"
            )

            if not path:
                self.log.warning("❌ Загрузка отменена")
                return

            self.log.info(f"📄 Выбран файл: {path}")
            self._load_data_from_path(path)

        except Exception as e:
            self.log.critical(f"❌ ОШИБКА: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", str(e))

    def _load_data_from_path(self, path: str):
        """Загружает данные из указанного пути"""
        self.log.info(f"→ _load_data_from_path({path})")
        self._show_loading(True)

        try:
            if not os.path.exists(path):
                self.log.error(f"❌ Файл не существует: {path}")
                QMessageBox.critical(self, "Ошибка", "Файл не найден")
                return

            file_size = os.path.getsize(path) / 1024 / 1024
            self.log.info(f"📊 Размер файла: {file_size:.2f} МБ")

            self.log.debug("Чтение файла...")
            if path.endswith('.csv'):
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path, engine='openpyxl')

            self.log.info(f"✅ Прочитано: {len(df)} строк")
            self.log.debug(f"Колонки: {df.columns.tolist()}")

            if len(df) == 0:
                self.log.warning("Файл пуст")
                QMessageBox.warning(self, "Предупреждение", "Файл пуст")
                return

            df.columns = [str(col).strip().lower() for col in df.columns]

            for col in ['date', 'status', 'category', 'omsu', 'mro']:
                if col not in df.columns:
                    self.log.warning(f"⚠️ Колонка '{col}' отсутствует, добавляем")
                    df[col] = 'Не указано'

            if 'date' in df.columns:
                try:
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                    valid_dates = df['date'].notna().sum()
                    self.log.info(f"📅 Валидных дат: {valid_dates} из {len(df)}")
                except Exception as e:
                    self.log.warning(f"Ошибка дат: {e}")

            if 'status' in df.columns:
                try:
                    df['status'] = df['status'].astype(str).str.lower().str.strip()
                    df['status'] = df['status'].apply(
                        lambda x: 'выполнено' if any(w in x for w in ['выполн', 'done', 'closed', 'закрыт', 'complete'])
                        else 'в работе' if any(w in x for w in ['работ', 'progress', 'open', 'ожида'])
                        else x
                    )
                except Exception as e:
                    self.log.warning(f"Ошибка статусов: {e}")

            self.data = df
            self.filtered_data = df.copy()
            self._current_df = df.copy()

            self.log.info(f"✅ Данные загружены: {len(df)} строк")
            self.info_label.setText(f"✅ {len(df)} строк")
            self.report_btn.setEnabled(True)

            self.build_dashboard()

        except Exception as e:
            self.log.critical(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            self.log.critical(traceback.format_exc())
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить:\n{str(e)}")
        finally:
            self._show_loading(False)

    def _show_loading(self, show: bool):
        """Показывает/скрывает полосу загрузки."""
        if show:
            self.progress_bar.show()
            self.load_btn.setEnabled(False)
            self.info_label.setText("⏳ Загрузка…")
        else:
            self.progress_bar.hide()
            self.load_btn.setEnabled(True)

    # ─── ПОСТРОЕНИЕ ДАШБОРДА ──────────────────────────────────────────────

    def build_dashboard(self):
        """Строит дашборд"""
        self.log.info("🏗️ Построение дашборда")

        if self._is_building:
            return

        self._is_building = True
        self._show_loading(True)

        try:
            df = self.filtered_data

            if df is None or len(df) == 0:
                self.show_welcome()
                return

            self.log.debug(f"Строим из {len(df)} строк")

            self._update_kpi(df)
            self._build_time_series(df)
            self._build_category_chart(df)
            self._build_categories(df)
            self._build_geography(df)
            self._build_trash(df)

            # После перестройки графиков — переприменяем цвета осей
            self.refresh_theme()

            self.log.info("✅ Дашборд построен")

        except Exception as e:
            self.log.critical(f"❌ Ошибка построения: {e}")
            self.log.critical(traceback.format_exc())
            QMessageBox.warning(self, "Ошибка", f"Не удалось построить дашборд:\n{str(e)}")

        finally:
            self._is_building = False
            self._show_loading(False)

    # ─── KPI ──────────────────────────────────────────────────────────────

    def _update_kpi(self, df):
        """Обновляет KPI"""
        self.log.debug("→ _update_kpi()")

        try:
            total = len(df)
            done = len(df[df['status'] == 'выполнено']) if 'status' in df.columns else 0
            in_progress = len(df[df['status'] == 'в работе']) if 'status' in df.columns else 0
            pct_done = f"{(done / total * 100):.1f}%" if total > 0 else "—"
            omsu_count = df['omsu'].nunique() if 'omsu' in df.columns else 0

            if 'date' in df.columns and len(df['date'].dropna()) > 0:
                period = f"{df['date'].min().strftime('%d.%m.%Y')} - {df['date'].max().strftime('%d.%m.%Y')}"
            else:
                period = "—"

            kpi_values = [
                f"{total:,}",
                f"{done:,}",
                f"{in_progress:,}",
                pct_done,
                f"{omsu_count:,}",
                period
            ]

            for i, (value_label, name_label) in enumerate(self.kpi_cards):
                value_label.setText(kpi_values[i])

            self.log.debug("← _update_kpi() завершён")

        except Exception as e:
            self.log.error(f"⚠️ Ошибка KPI: {e}")

    # ─── ВРЕМЕННОЙ РЯД ────────────────────────────────────────────────────

    def _build_time_series(self, df):
        """Строит временной ряд с реальными датами на оси X."""
        self.log.debug("→ _build_time_series()")

        try:
            self.ts_plot.clear()

            if 'date' not in df.columns:
                self.log.warning("⚠️ Нет колонки date")
                self.ts_plot.addItem(pg.TextItem("Нет данных с датой", color=(150, 150, 150)))
                return

            df_valid = df[df['date'].notna()].copy()
            if len(df_valid) == 0:
                self.ts_plot.addItem(pg.TextItem("Нет валидных дат", color=(150, 150, 150)))
                return

            df_valid['date_day'] = df_valid['date'].dt.normalize()
            settings = self.chart_settings.get('time_series', {})

            if 'status' in df_valid.columns:
                statuses = ['выполнено', 'в работе']
                series_data = {}
                for status in statuses:
                    sub = df_valid[df_valid['status'] == status]
                    if len(sub):
                        daily = sub.groupby('date_day').size().sort_index()
                        series_data[status] = daily
                self._ts_all_data = {'type': 'multi', 'series': series_data, 'settings': settings}
            else:
                daily = df_valid.groupby('date_day').size().sort_index()
                self._ts_all_data = {'type': 'single', 'series': daily, 'settings': settings}

            self._ts_render()
            self.log.info("✅ Временной ряд построен")

        except Exception as e:
            self.log.error(f"⚠️ Ошибка временного ряда: {e}")
            traceback.print_exc()
            self.ts_plot.addItem(pg.TextItem(f"Ошибка: {str(e)[:40]}", color=(200, 50, 50)))

    def _ts_set_period(self, days: int):
        """Переключает отображаемый период на графике (0 = всё)."""
        self._ts_active_days = days
        for btn, d in self._period_buttons:
            btn.setChecked(d == days)
        self._ts_render()

    def _ts_render(self):
        """Перерисовывает время с учётом текущего периода."""
        if not self._ts_all_data:
            return

        self.ts_plot.clear()
        settings = self._ts_all_data.get('settings', {})
        days = getattr(self, '_ts_active_days', 0)

        def _filter(series):
            if days <= 0 or len(series) == 0:
                return series
            cutoff = series.index.max() - pd.Timedelta(days=days)
            return series[series.index >= cutoff]

        def _to_timestamps(series):
            return series.index.astype('int64') // 10**9

        line_width = settings.get('line_width', 2)
        point_size = settings.get('point_size', 4)

        if self._ts_all_data['type'] == 'multi':
            colors_map = {'выполнено': (40, 167, 69), 'в работе': (253, 126, 20)}
            legend = self.ts_plot.addLegend()
            any_plotted = False
            for status, series in self._ts_all_data['series'].items():
                filt = _filter(series)
                if len(filt) == 0:
                    continue
                x = _to_timestamps(filt)
                y = filt.values.astype(float)
                color = colors_map.get(status, (100, 100, 100))
                self.ts_plot.plot(x, y,
                    pen=pg.mkPen(color=color, width=line_width),
                    name=status)
                any_plotted = True
            if not any_plotted:
                self.ts_plot.addItem(pg.TextItem("Нет данных за выбранный период",
                                                  color=(150, 150, 150)))
        else:
            series = _filter(self._ts_all_data['series'])
            if len(series) == 0:
                self.ts_plot.addItem(pg.TextItem("Нет данных за выбранный период",
                                                  color=(150, 150, 150)))
                return
            x = _to_timestamps(series)
            y = series.values.astype(float)
            self.ts_plot.plot(x, y,
                pen=pg.mkPen(color=(40, 167, 69), width=line_width),
                symbol='o', symbolSize=point_size,
                symbolBrush=(40, 167, 69))

        self.ts_plot.setLabel('left', settings.get('y_label', 'Количество'))
        self.ts_plot.setLabel('bottom', settings.get('x_label', 'Дата'))
        self.ts_plot.autoRange()

    # ─── ГРАФИК КАТЕГОРИЙ ──────────────────────────────────────────────────

    def _build_category_chart(self, df):
        """Строит график категорий (для обзора) с учётом настроек"""
        self.log.debug("→ _build_category_chart()")

        try:
            self.plot.clear()

            if 'category' not in df.columns:
                self.log.warning("⚠️ Нет колонки category")
                text = pg.TextItem("Нет данных", color=(150, 150, 150))
                self.plot.addItem(text)
                return

            settings = self.chart_settings.get('top_categories', {})

            counts = df['category'].value_counts().head(settings.get('limit', 10) or 10)

            if len(counts) == 0:
                text = pg.TextItem("Нет данных", color=(150, 150, 150))
                self.plot.addItem(text)
                return

            sort_order = settings.get('sort_order', 'По убыванию')
            if sort_order == 'По возрастанию':
                counts = counts.sort_values(ascending=True)

            bars = pg.BarGraphItem(
                x=np.arange(len(counts)),
                height=counts.values,
                width=0.6,
                brush=pg.mkBrush(settings.get('main_color', _tm.ACCENT_DARK))
            )
            self.plot.addItem(bars)

            ticks = [[(i, str(name)[:15]) for i, name in enumerate(counts.index)]]
            self.plot.getAxis('bottom').setTicks(ticks)
            self.plot.setXRange(-0.5, len(counts) - 0.5)
            self.plot.setLabel('left', settings.get('y_label', 'Количество'))
            self.plot.setLabel('bottom', settings.get('x_label', 'Категория'))

            self._apply_chart_settings(self.plot, 'top_categories', settings)

            self.log.info(f"✅ Построен график с {len(counts)} категориями")

        except Exception as e:
            self.log.error(f"⚠️ Ошибка графика категорий: {e}")
            traceback.print_exc()

    # ─── КАТЕГОРИИ (ТАБЛИЦА + ГРАФИК) ─────────────────────────────────────

    def _build_categories(self, df):
        """Строит таблицу и график категорий"""
        self.log.debug("→ _build_categories()")

        try:
            self.cat_plot.clear()

            if 'category' not in df.columns:
                self.log.warning("⚠️ Нет колонки category")
                text = pg.TextItem("Нет данных", color=(150, 150, 150))
                self.cat_plot.addItem(text)
                return

            settings = self.chart_settings.get('categories_chart', {})

            counts = df['category'].value_counts().reset_index()
            counts.columns = ['Категория', 'Всего']
            counts['Доля %'] = (counts['Всего'] / counts['Всего'].sum() * 100).round(1)

            if 'status' in df.columns:
                done = df[df['status'] == 'выполнено']['category'].value_counts()
                in_progress = df[df['status'] == 'в работе']['category'].value_counts()
                counts['Выполнено'] = counts['Категория'].map(done).fillna(0).astype(int)
                counts['В работе'] = counts['Категория'].map(in_progress).fillna(0).astype(int)
            else:
                counts['Выполнено'] = 0
                counts['В работе'] = 0

            limit = settings.get('limit', 0)
            if limit > 0:
                counts = counts.head(limit)

            sort_order = settings.get('sort_order', 'По убыванию')
            if sort_order == 'По возрастанию':
                counts = counts.sort_values('Всего', ascending=True)

            self.cat_table.setRowCount(len(counts))
            for i, row in counts.iterrows():
                self.cat_table.setItem(i, 0, QTableWidgetItem(str(row['Категория'])))
                self.cat_table.setItem(i, 1, QTableWidgetItem(str(row['Всего'])))
                self.cat_table.setItem(i, 2, QTableWidgetItem(f"{row['Доля %']:.1f}%"))
                self.cat_table.setItem(i, 3, QTableWidgetItem(str(row.get('Выполнено', 0))))
                self.cat_table.setItem(i, 4, QTableWidgetItem(str(row.get('В работе', 0))))

            if len(counts) > 0:
                bars = pg.BarGraphItem(
                    x=np.arange(len(counts)),
                    height=counts['Всего'].values,
                    width=0.6,
                    brush=pg.mkBrush(settings.get('main_color', _tm.ACCENT_DARK))
                )
                self.cat_plot.addItem(bars)

                ticks = [[(i, str(name)[:15]) for i, name in enumerate(counts['Категория'].values)]]
                self.cat_plot.getAxis('bottom').setTicks(ticks)
                self.cat_plot.setXRange(-0.5, len(counts) - 0.5)
                self.cat_plot.setLabel('left', settings.get('y_label', 'Количество'))
                self.cat_plot.setLabel('bottom', settings.get('x_label', 'Категория'))

            self._apply_chart_settings(self.cat_plot, 'categories_chart', settings)

            self.log.info(f"✅ Категории построены: {len(counts)} записей")

        except Exception as e:
            self.log.error(f"⚠️ Ошибка категорий: {e}")
            traceback.print_exc()

    # ─── ГЕОГРАФИЯ ─────────────────────────────────────────────────────────

    def _build_geography(self, df):
        """Строит географию"""
        self.log.debug("→ _build_geography()")
        try:
            self.update_geography()
        except Exception as e:
            self.log.error(f"⚠️ Ошибка географии: {e}")
            traceback.print_exc()

    def update_geography(self):
        """Обновляет географию"""
        self.log.debug("→ update_geography()")

        try:
            self.geo_plot.clear()

            if self.filtered_data is None or len(self.filtered_data) == 0:
                text = pg.TextItem("Нет данных", color=(150, 150, 150))
                self.geo_plot.addItem(text)
                return

            df = self.filtered_data
            geo_type = self.geo_type.currentText()
            settings = self.chart_settings.get('geography_chart', {})

            if geo_type == "По ОМСУ":
                col = 'omsu'
                name_col = "ОМСУ"
            else:
                col = 'mro'
                name_col = "МРО"

            if col not in df.columns:
                text = pg.TextItem(f"Нет данных по {name_col}", color=(150, 150, 150))
                self.geo_plot.addItem(text)
                return

            counts = df[col].value_counts().reset_index()
            counts.columns = [name_col, 'Всего']
            counts['Доля %'] = (counts['Всего'] / counts['Всего'].sum() * 100).round(1)

            if 'status' in df.columns:
                done = df[df['status'] == 'выполнено'][col].value_counts()
                in_progress = df[df['status'] == 'в работе'][col].value_counts()
                counts['Выполнено'] = counts[name_col].map(done).fillna(0).astype(int)
                counts['В работе'] = counts[name_col].map(in_progress).fillna(0).astype(int)
            else:
                counts['Выполнено'] = 0
                counts['В работе'] = 0

            counts['Бэклог %'] = (counts['В работе'] / counts['Всего'].replace(0, pd.NA) * 100).round(1).fillna(0.0)

            limit = settings.get('limit', 10) or 10
            counts = counts.head(limit)

            sort_order = settings.get('sort_order', 'По убыванию')
            if sort_order == 'По возрастанию':
                counts = counts.sort_values('Всего', ascending=True)

            self.geo_table.setRowCount(len(counts))
            for i, row in counts.iterrows():
                self.geo_table.setItem(i, 0, QTableWidgetItem(str(row[name_col])))
                self.geo_table.setItem(i, 1, QTableWidgetItem(str(row['Всего'])))
                self.geo_table.setItem(i, 2, QTableWidgetItem(f"{row['Доля %']:.1f}%"))
                self.geo_table.setItem(i, 3, QTableWidgetItem(str(row.get('Выполнено', 0))))
                self.geo_table.setItem(i, 4, QTableWidgetItem(str(row.get('В работе', 0))))
                self.geo_table.setItem(i, 5, QTableWidgetItem(f"{row.get('Бэклог %', 0):.1f}%"))

            if len(counts) > 0:
                bars = pg.BarGraphItem(
                    x=np.arange(len(counts)),
                    height=counts['Всего'].values,
                    width=0.6,
                    brush=pg.mkBrush(settings.get('main_color', _tm.ACCENT_DARK))
                )
                self.geo_plot.addItem(bars)

                ticks = [[(i, str(name)[:12]) for i, name in enumerate(counts[name_col].values)]]
                self.geo_plot.getAxis('bottom').setTicks(ticks)
                self.geo_plot.setXRange(-0.5, len(counts) - 0.5)
                self.geo_plot.setLabel('left', settings.get('y_label', 'Количество'))
                self.geo_plot.setLabel('bottom', settings.get('x_label', name_col))

            self._apply_chart_settings(self.geo_plot, 'geography_chart', settings)

            self.log.debug("← update_geography() завершён")

        except Exception as e:
            self.log.error(f"⚠️ Ошибка обновления географии: {e}")
            traceback.print_exc()

    # ─── МУСОР ─────────────────────────────────────────────────────────────

    def _build_trash(self, df):
        """Строит аналитику по мусору"""
        self.log.debug("→ _build_trash()")

        try:
            self.trash_plot.clear()

            if 'omsu' not in df.columns or 'category' not in df.columns:
                self.log.warning("⚠️ Нет колонок omsu или category")
                text = pg.TextItem("Нет данных", color=(150, 150, 150))
                self.trash_plot.addItem(text)
                return

            settings = self.chart_settings.get('trash_chart', {})

            trash_keywords = ['мусор', 'свалк', 'сток', 'отход']
            mask = df['category'].str.contains('|'.join(trash_keywords), case=False, na=False)
            trash_df = df[mask].copy()

            if len(trash_df) == 0:
                self.log.warning("⚠️ Нет данных по мусору")
                text = pg.TextItem("Нет данных по мусору", color=(150, 150, 150))
                self.trash_plot.addItem(text)
                return

            counts = trash_df['omsu'].value_counts().reset_index()
            counts.columns = ['ОМСУ', 'Всего']
            counts['Доля %'] = (counts['Всего'] / counts['Всего'].sum() * 100).round(1)

            if 'status' in trash_df.columns:
                done = trash_df[trash_df['status'] == 'выполнено']['omsu'].value_counts()
                in_progress = trash_df[trash_df['status'] == 'в работе']['omsu'].value_counts()
                counts['Выполнено'] = counts['ОМСУ'].map(done).fillna(0).astype(int)
                counts['В работе'] = counts['ОМСУ'].map(in_progress).fillna(0).astype(int)
            else:
                counts['Выполнено'] = 0
                counts['В работе'] = 0

            counts['Бэклог %'] = (counts['В работе'] / counts['Всего'].replace(0, pd.NA) * 100).round(1).fillna(0.0)

            top_count = counts.sort_values('Всего', ascending=False).reset_index(drop=True)
            top_backlog = counts.sort_values('Бэклог %', ascending=False).reset_index(drop=True)

            limit = settings.get('limit', 10) or 10
            top_count = top_count.head(limit)
            top_backlog = top_backlog.head(limit)

            sort_order = settings.get('sort_order', 'По убыванию')
            if sort_order == 'По возрастанию':
                top_count = top_count.sort_values('Всего', ascending=True)
                top_backlog = top_backlog.sort_values('Бэклог %', ascending=True)

            self.trash_count_table.setRowCount(len(top_count))
            for i, row in top_count.iterrows():
                self.trash_count_table.setItem(i, 0, QTableWidgetItem(str(row['ОМСУ'])))
                self.trash_count_table.setItem(i, 1, QTableWidgetItem(str(row['Всего'])))
                self.trash_count_table.setItem(i, 2, QTableWidgetItem(f"{row['Доля %']:.1f}%"))
                self.trash_count_table.setItem(i, 3, QTableWidgetItem(str(row.get('Выполнено', 0))))
                self.trash_count_table.setItem(i, 4, QTableWidgetItem(str(row.get('В работе', 0))))
                self.trash_count_table.setItem(i, 5, QTableWidgetItem(f"{row.get('Бэклог %', 0):.1f}%"))

            self.trash_backlog_table.setRowCount(len(top_backlog))
            for i, row in top_backlog.iterrows():
                self.trash_backlog_table.setItem(i, 0, QTableWidgetItem(str(row['ОМСУ'])))
                self.trash_backlog_table.setItem(i, 1, QTableWidgetItem(str(row['Всего'])))
                self.trash_backlog_table.setItem(i, 2, QTableWidgetItem(f"{row['Доля %']:.1f}%"))
                self.trash_backlog_table.setItem(i, 3, QTableWidgetItem(str(row.get('Выполнено', 0))))
                self.trash_backlog_table.setItem(i, 4, QTableWidgetItem(str(row.get('В работие', 0))))
                self.trash_backlog_table.setItem(i, 5, QTableWidgetItem(f"{row.get('Бэклог %', 0):.1f}%"))

            if len(top_count) > 0:
                bars = pg.BarGraphItem(
                    x=np.arange(len(top_count)),
                    height=top_count['Всего'].values,
                    width=0.6,
                    brush=pg.mkBrush(settings.get('main_color', _tm.ACCENT_RED))
                )
                self.trash_plot.addItem(bars)

                ticks = [[(i, str(name)[:12]) for i, name in enumerate(top_count['ОМСУ'].values)]]
                self.trash_plot.getAxis('bottom').setTicks(ticks)
                self.trash_plot.setXRange(-0.5, len(top_count) - 0.5)
                self.trash_plot.setLabel('left', settings.get('y_label', 'Количество'))
                self.trash_plot.setLabel('bottom', settings.get('x_label', 'ОМСУ'))
                self.trash_plot.setTitle('Топ ОМСУ по обращениям "Мусор, свалки, стоки"')

            self._apply_chart_settings(self.trash_plot, 'trash_chart', settings)

            self.log.info(f"✅ Аналитика мусора построена: {len(top_count)} записей")

        except Exception as e:
            self.log.error(f"⚠️ Ошибка аналитики мусора: {e}")
            traceback.print_exc()
            text = pg.TextItem(f"Ошибка: {str(e)[:30]}", color=(200, 50, 50))
            self.trash_plot.addItem(text)

    # ─── ЭКСПОРТ ──────────────────────────────────────────────────────────

    def export_report(self):
        """Экспортирует отчёт"""
        self.log.debug("→ export_report()")

        try:
            if self.filtered_data is None or len(self.filtered_data) == 0:
                self.log.warning("⚠️ Нет данных для экспорта")
                return

            path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить отчёт", "eco_report.xlsx", "Excel (*.xlsx)"
            )
            if not path:
                self.log.warning("❌ Экспорт отменён")
                return

            self.filtered_data.to_excel(path, index=False)
            self.log.info(f"✅ Отчёт сохранён: {path}")
            QMessageBox.information(self, "Успех", f"Отчёт сохранён:\n{path}")

        except Exception as e:
            self.log.error(f"❌ Ошибка экспорта: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить отчёт:\n{str(e)}")

    def go_back(self):
        self.log.info("⬅️ Возврат")
        self.back_clicked.emit()
