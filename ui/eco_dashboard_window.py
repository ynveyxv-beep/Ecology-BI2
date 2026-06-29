from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QScrollArea,
    QTabWidget, QComboBox, QDateEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QGridLayout, QGroupBox, QFrame, QSizePolicy
)
from PySide6.QtGui import QFont

import pandas as pd
import numpy as np
import pyqtgraph as pg
import traceback

# ─── Импорт модулей Славика ──────────────────────────────────────────────
try:
    from eco_modules import (
        get_kpi, get_by_category, get_by_omsu, get_by_mro,
        get_time_series, get_trash_analysis, load_excel, export_excel
    )
    ECO_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ eco_modules not available: {e}")
    ECO_MODULES_AVAILABLE = False
    
    def get_kpi(df):
        return {'total': len(df), 'done': 0, 'in_progress': 0, 'pct_done': '—', 
                'omsu_count': 0, 'category_count': 0, 'period': '—'}
    
    def get_by_category(df):
        return pd.DataFrame(columns=["Категория", "Всего", "Доля %", "Выполнено", "В работе"])
    
    def get_by_omsu(df):
        return pd.DataFrame(columns=["ОМСУ", "Всего", "Доля %", "Выполнено", "В работе", "Бэклог %"])
    
    def get_by_mro(df):
        return pd.DataFrame(columns=["МРО", "Всего", "Доля %", "Выполнено", "В работе"])
    
    def get_time_series(df, freq='D'):
        return pd.DataFrame(columns=["Дата", "Выполнено", "В работе"])
    
    def get_trash_analysis(df):
        return (pd.DataFrame(columns=["ОМСУ", "Всего", "Доля %", "Выполнено", "В работе", "Бэклог %"]),
                pd.DataFrame(columns=["ОМСУ", "Всего", "Доля %", "Выполнено", "В работе", "Бэклог %"]))


class EcoDashboardWindow(QWidget):
    """Экологический дашборд — стабильная версия"""
    
    back_clicked = Signal()
    
    def __init__(self):
        super().__init__()
        self.data = None
        self.filtered_data = None
        self._is_building = False
        self._widgets_created = False
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ─── Верхняя панель ─────────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setStyleSheet("background: #f8f9fa; padding: 5px; border-bottom: 1px solid #dee2e6;")
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
        
        self.info_label = QLabel("Данные не загружены")
        self.info_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        toolbar_layout.addWidget(self.info_label)
        
        main_layout.addWidget(toolbar)
        
        # ─── Фильтры ────────────────────────────────────────────────────────
        self.filters_widget = QWidget()
        self.filters_widget.setStyleSheet("background: white; padding: 5px; border-bottom: 1px solid #dee2e6;")
        filters_layout = QHBoxLayout(self.filters_widget)
        filters_layout.setContentsMargins(10, 5, 10, 5)
        filters_layout.setSpacing(10)
        
        filters_layout.addWidget(QLabel("📅 Период:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd.MM.yyyy")
        self.date_from.setSpecialValueText("с")
        filters_layout.addWidget(self.date_from)
        
        filters_layout.addWidget(QLabel("—"))
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd.MM.yyyy")
        self.date_to.setSpecialValueText("по")
        filters_layout.addWidget(self.date_to)
        
        filters_layout.addWidget(QLabel("|"))
        
        filters_layout.addWidget(QLabel("Категория:"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("Все")
        self.category_filter.currentTextChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.category_filter)
        
        filters_layout.addWidget(QLabel("|"))
        
        filters_layout.addWidget(QLabel("Статус:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Все", "выполнено", "в работе"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.status_filter)
        
        filters_layout.addStretch()
        
        reset_btn = QPushButton("🔄 Сбросить")
        reset_btn.clicked.connect(self.reset_filters)
        filters_layout.addWidget(reset_btn)
        
        main_layout.addWidget(self.filters_widget)
        
        # ─── Вкладки ──────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: #f5f5f5; }
            QTabBar::tab { padding: 8px 16px; background: #e9ecef; border: none; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: white; font-weight: bold; }
        """)
        
        # Создаём вкладки и сразу заполняем их (без динамического удаления)
        self.tab_overview = QWidget()
        self.tab_categories = QWidget()
        self.tab_geography = QWidget()
        self.tab_trash = QWidget()
        
        self.tabs.addTab(self.tab_overview, "📊 Обзор")
        self.tabs.addTab(self.tab_categories, "📋 Категории")
        self.tabs.addTab(self.tab_geography, "🗺️ География")
        self.tabs.addTab(self.tab_trash, "♻️ Мусор")
        
        main_layout.addWidget(self.tabs)
        
        # ─── Создаём все виджеты один раз ────────────────────────────────
        self._create_overview_widgets()
        self._create_categories_widgets()
        self._create_geography_widgets()
        self._create_trash_widgets()
        
        self._widgets_created = True
        
        # Показываем приветствие
        self.show_welcome()
    
    # ─── СОЗДАНИЕ ВИДЖЕТОВ (один раз) ────────────────────────────────────
    
    def _create_overview_widgets(self):
        """Создаёт виджеты для вкладки Обзор"""
        layout = QVBoxLayout(self.tab_overview)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # KPI-карточки
        self.kpi_container = QWidget()
        self.kpi_layout = QHBoxLayout(self.kpi_container)
        self.kpi_layout.setSpacing(10)
        layout.addWidget(self.kpi_container)
        
        # Графики
        charts_row = QHBoxLayout()
        charts_row.setSpacing(15)
        
        # Динамика
        self.ts_container = QWidget()
        self.ts_layout = QVBoxLayout(self.ts_container)
        self.ts_layout.setContentsMargins(0, 0, 0, 0)
        self.ts_label = QLabel("📈 Динамика обращений")
        self.ts_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.ts_layout.addWidget(self.ts_label)
        self.ts_plot = pg.PlotWidget()
        self.ts_plot.setBackground('white')
        self.ts_plot.setMinimumHeight(250)
        self.ts_layout.addWidget(self.ts_plot)
        charts_row.addWidget(self.ts_container, 2)
        
        # Топ категорий
        self.top_cat_container = QWidget()
        self.top_cat_layout = QVBoxLayout(self.top_cat_container)
        self.top_cat_layout.setContentsMargins(0, 0, 0, 0)
        self.top_cat_label = QLabel("🏆 Топ категорий")
        self.top_cat_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.top_cat_layout.addWidget(self.top_cat_label)
        self.top_cat_plot = pg.PlotWidget()
        self.top_cat_plot.setBackground('white')
        self.top_cat_plot.setMinimumHeight(250)
        self.top_cat_layout.addWidget(self.top_cat_plot)
        charts_row.addWidget(self.top_cat_container, 1)
        
        layout.addLayout(charts_row)
        
        # Топ ОМСУ
        self.top_omsu_container = QWidget()
        self.top_omsu_layout = QVBoxLayout(self.top_omsu_container)
        self.top_omsu_layout.setContentsMargins(0, 0, 0, 0)
        self.top_omsu_label = QLabel("🏆 Топ ОМСУ")
        self.top_omsu_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.top_omsu_layout.addWidget(self.top_omsu_label)
        self.top_omsu_plot = pg.PlotWidget()
        self.top_omsu_plot.setBackground('white')
        self.top_omsu_plot.setMinimumHeight(250)
        self.top_omsu_layout.addWidget(self.top_omsu_plot)
        layout.addWidget(self.top_omsu_container)
    
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
        self.cat_plot.setMinimumHeight(300)
        layout.addWidget(self.cat_plot)
    
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
        self.geo_plot.setMinimumHeight(300)
        layout.addWidget(self.geo_plot)
    
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
        self.trash_plot.setMinimumHeight(250)
        layout.addWidget(self.trash_plot)
    
    # ─── ОТОБРАЖЕНИЕ ДАННЫХ ──────────────────────────────────────────────
    
    def show_welcome(self):
        """Показывает приветствие"""
        # Просто очищаем виджеты через их методы
        self.kpi_layout = QHBoxLayout(self.kpi_container)
        self.kpi_layout.setSpacing(10)
        
        self.ts_plot.clear()
        self.top_cat_plot.clear()
        self.top_omsu_plot.clear()
        self.cat_plot.clear()
        self.geo_plot.clear()
        self.trash_plot.clear()
        
        # Добавляем приветствие на вкладки через QLabel
        self._show_message_on_tab(self.tab_overview, "🌿 Загрузите данные для отображения дашборда")
        self._show_message_on_tab(self.tab_categories, "🌿 Загрузите данные для отображения дашборда")
        self._show_message_on_tab(self.tab_geography, "🌿 Загрузите данные для отображения дашборда")
        self._show_message_on_tab(self.tab_trash, "🌿 Загрузите данные для отображения дашборда")
    
    def _show_message_on_tab(self, tab, message):
        """Показывает сообщение на вкладке"""
        # Ищем существующий label
        for i in range(tab.layout().count()):
            widget = tab.layout().itemAt(i).widget()
            if isinstance(widget, QLabel) and "Загрузите" in widget.text():
                widget.setText(message)
                widget.setAlignment(Qt.AlignCenter)
                widget.setStyleSheet("font-size: 18px; color: #888; padding: 40px;")
                return
        
        # Если нет — создаём
        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: #888; padding: 40px;")
        tab.layout().insertWidget(0, label)
    
    def load_data(self):
        """Загружает данные"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Загрузить данные", "", "Excel (*.xlsx *.xls);;CSV (*.csv)"
        )
        if not path:
            return
        
        try:
            if path.endswith('.csv'):
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)
            
            if df is None or len(df) == 0:
                QMessageBox.warning(self, "Предупреждение", "Файл пуст")
                return
            
            # Нормализуем колонки
            df.columns = [str(col).strip().lower() for col in df.columns]
            
            # Создаём необходимые колонки
            for col in ['date', 'status', 'category', 'omsu', 'mro']:
                if col not in df.columns:
                    df[col] = 'Не указано'
            
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            
            if 'status' in df.columns:
                df['status'] = df['status'].astype(str).str.lower().str.strip()
                df['status'] = df['status'].apply(
                    lambda x: 'выполнено' if any(w in x for w in ['выполн', 'done', 'closed', 'закрыт', 'complete'])
                    else 'в работе' if any(w in x for w in ['работ', 'progress', 'open', 'ожида'])
                    else 'Не указано'
                )
            
            if 'category' in df.columns:
                df['category'] = df['category'].fillna('Не указано')
            
            self.data = df
            self.filtered_data = df.copy()
            
            self._update_filters()
            
            self.report_btn.setEnabled(True)
            self.info_label.setText(f"✅ {len(self.data)} строк, {len(self.data.columns)} колонок")
            
            self.build_dashboard()
            
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные:\n{str(e)}")
    
    def _update_filters(self):
        """Обновляет фильтры"""
        try:
            if self.data is None:
                return
            
            self.category_filter.clear()
            self.category_filter.addItem("Все")
            if 'category' in self.data.columns:
                cats = sorted(self.data['category'].dropna().unique())
                for cat in cats:
                    if cat and cat != 'Не указано':
                        self.category_filter.addItem(cat)
            
            if 'date' in self.data.columns and len(self.data['date'].dropna()) > 0:
                min_date = self.data['date'].min()
                max_date = self.data['date'].max()
                if pd.notna(min_date) and pd.notna(max_date):
                    from PySide6.QtCore import QDate
                    self.date_from.setDate(QDate(min_date.year, min_date.month, min_date.day))
                    self.date_to.setDate(QDate(max_date.year, max_date.month, max_date.day))
        except Exception as e:
            print(f"⚠️ Update filters error: {e}")
    
    def reset_filters(self):
        """Сбрасывает фильтры"""
        try:
            self.status_filter.setCurrentIndex(0)
            self.category_filter.setCurrentIndex(0)
            self.date_from.setSpecialValueText("с")
            self.date_to.setSpecialValueText("по")
            self.apply_filters()
        except Exception as e:
            print(f"⚠️ Reset filters error: {e}")
    
    def apply_filters(self):
        """Применяет фильтры"""
        try:
            if self.data is None:
                return
            
            df = self.data.copy()
            
            if self.date_from.date().isValid() and self.date_to.date().isValid():
                from PySide6.QtCore import QDate
                date_from = QDate(self.date_from.date().year(), self.date_from.date().month(), self.date_from.date().day())
                date_to = QDate(self.date_to.date().year(), self.date_to.date().month(), self.date_to.date().day())
                
                if 'date' in df.columns:
                    mask = (df['date'] >= pd.Timestamp(date_from.toPython())) & (df['date'] <= pd.Timestamp(date_to.toPython()))
                    df = df[mask]
            
            status = self.status_filter.currentText()
            if status != "Все" and 'status' in df.columns:
                df = df[df['status'] == status]
            
            category = self.category_filter.currentText()
            if category != "Все" and 'category' in df.columns:
                df = df[df['category'] == category]
            
            self.filtered_data = df
            self.build_dashboard()
            
        except Exception as e:
            print(f"⚠️ Apply filters error: {e}")
            traceback.print_exc()
    
    # ─── ПОСТРОЕНИЕ ДАШБОРДА ──────────────────────────────────────────────
    
    def build_dashboard(self):
        """Строит дашборд"""
        if self._is_building:
            return
        
        self._is_building = True
        
        try:
            df = self.filtered_data
            
            if df is None or len(df) == 0:
                self.show_welcome()
                return
            
            # Убираем приветственные сообщения
            self._clear_welcome_messages()
            
            # Строим каждый компонент
            self._build_kpi(df)
            self._build_time_series(df)
            self._build_top_categories(df)
            self._build_top_omsu(df)
            self._build_categories_table(df)
            self._build_geography(df)
            self._build_trash(df)
            
        except Exception as e:
            print(f"❌ Build dashboard error: {e}")
            traceback.print_exc()
        
        finally:
            self._is_building = False
    
    def _clear_welcome_messages(self):
        """Убирает приветственные сообщения со всех вкладок"""
        for tab in [self.tab_overview, self.tab_categories, self.tab_geography, self.tab_trash]:
            for i in range(tab.layout().count()):
                widget = tab.layout().itemAt(i).widget()
                if isinstance(widget, QLabel) and "Загрузите" in widget.text():
                    widget.deleteLater()
    
    # ─── KPI ────────────────────────────────────────────────────────────────
    
    def _build_kpi(self, df):
        """Строит KPI-карточки"""
        try:
            # Очищаем существующие карточки
            while self.kpi_layout.count():
                item = self.kpi_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            kpi = get_kpi(df)
            
            kpi_data = [
                ("Всего", f"{kpi['total']:,}", "#1F4E79"),
                ("Выполнено", f"{kpi['done']:,}", "#28a745"),
                ("В работе", f"{kpi['in_progress']:,}", "#fd7e14"),
                ("% выполнения", kpi['pct_done'], "#17a2b8"),
                ("ОМСУ", f"{kpi['omsu_count']:,}", "#6c757d"),
                ("Период", kpi['period'], "#343a40"),
            ]
            
            for label, value, color in kpi_data:
                card = QWidget()
                card.setFixedHeight(75)
                card.setMinimumWidth(100)
                card.setStyleSheet(f"""
                    background-color: {color};
                    border-radius: 8px;
                    padding: 5px 10px;
                """)
                card_layout = QVBoxLayout(card)
                card_layout.setContentsMargins(10, 5, 10, 5)
                
                val_label = QLabel(str(value))
                val_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
                val_label.setAlignment(Qt.AlignCenter)
                card_layout.addWidget(val_label)
                
                name_label = QLabel(label)
                name_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 11px;")
                name_label.setAlignment(Qt.AlignCenter)
                card_layout.addWidget(name_label)
                
                self.kpi_layout.addWidget(card)
            
            self.kpi_layout.addStretch()
            
        except Exception as e:
            print(f"⚠️ KPI error: {e}")
    
    # ─── Временной ряд ─────────────────────────────────────────────────────
    
    def _build_time_series(self, df):
        """Строит график временного ряда"""
        try:
            self.ts_plot.clear()
            
            if 'date' not in df.columns:
                text = pg.TextItem("Нет данных с датой", color=(150, 150, 150))
                self.ts_plot.addItem(text)
                return
            
            ts = get_time_series(df, 'D')
            if len(ts) == 0:
                text = pg.TextItem("Нет данных", color=(150, 150, 150))
                self.ts_plot.addItem(text)
                return
            
            dates = ts["Дата"].dt.strftime("%d.%m")
            
            if "В работе" in ts.columns:
                self.ts_plot.plot(
                    dates, ts["В работе"],
                    pen=pg.mkPen(color=(253, 126, 20), width=2),
                    name="В работе"
                )
            if "Выполнено" in ts.columns:
                self.ts_plot.plot(
                    dates, ts["Выполнено"],
                    pen=pg.mkPen(color=(40, 167, 69), width=2),
                    name="Выполнено"
                )
            
            self.ts_plot.addLegend()
            self.ts_plot.setLabel('left', 'Количество')
            self.ts_plot.setLabel('bottom', 'Дата')
            
        except Exception as e:
            print(f"⚠️ Time series error: {e}")
    
    # ─── Топ категорий ─────────────────────────────────────────────────────
    
    def _build_top_categories(self, df):
        """Строит график топ-категорий"""
        try:
            self.top_cat_plot.clear()
            
            cat = get_by_category(df)
            if len(cat) == 0:
                text = pg.TextItem("Нет данных", color=(150, 150, 150))
                self.top_cat_plot.addItem(text)
                return
            
            cat = cat.head(8)
            names = cat["Категория"].tolist()
            values = cat["Всего"].tolist()
            
            bars = pg.BarGraphItem(
                x=np.arange(len(names)),
                height=values,
                width=0.6,
                brush=pg.mkBrush(0, 120, 215)
            )
            self.top_cat_plot.addItem(bars)
            self.top_cat_plot.setLabel('left', 'Количество')
            self.top_cat_plot.getAxis('bottom').setTicks([[(i, name[:12]) for i, name in enumerate(names)]])
            self.top_cat_plot.setXRange(-0.5, len(names) - 0.5)
            
        except Exception as e:
            print(f"⚠️ Top categories error: {e}")
    
    # ─── Топ ОМСУ ──────────────────────────────────────────────────────────
    
    def _build_top_omsu(self, df):
        """Строит график топ-ОМСУ"""
        try:
            self.top_omsu_plot.clear()
            
            omsu = get_by_omsu(df)
            if len(omsu) == 0:
                text = pg.TextItem("Нет данных", color=(150, 150, 150))
                self.top_omsu_plot.addItem(text)
                return
            
            omsu = omsu.head(8)
            names = omsu["ОМСУ"].tolist()
            values = omsu["Всего"].tolist()
            
            bars = pg.BarGraphItem(
                x=np.arange(len(names)),
                height=values,
                width=0.6,
                brush=pg.mkBrush(46, 134, 171)
            )
            self.top_omsu_plot.addItem(bars)
            self.top_omsu_plot.setLabel('left', 'Количество')
            self.top_omsu_plot.getAxis('bottom').setTicks([[(i, name[:12]) for i, name in enumerate(names)]])
            self.top_omsu_plot.setXRange(-0.5, len(names) - 0.5)
            
        except Exception as e:
            print(f"⚠️ Top OMSU error: {e}")
    
    # ─── Таблица категорий ─────────────────────────────────────────────────
    
    def _build_categories_table(self, df):
        """Строит таблицу категорий"""
        try:
            cat = get_by_category(df)
            
            self.cat_table.setRowCount(len(cat))
            for i, row in cat.iterrows():
                self.cat_table.setItem(i, 0, QTableWidgetItem(str(row["Категория"])))
                self.cat_table.setItem(i, 1, QTableWidgetItem(str(row["Всего"])))
                self.cat_table.setItem(i, 2, QTableWidgetItem(f"{row['Доля %']:.1f}%"))
                self.cat_table.setItem(i, 3, QTableWidgetItem(str(row["Выполнено"])))
                self.cat_table.setItem(i, 4, QTableWidgetItem(str(row["В работе"])))
            
            # График категорий
            self.cat_plot.clear()
            if len(cat) > 0:
                names = cat["Категория"].tolist()
                values = cat["Всего"].tolist()
                bars = pg.BarGraphItem(
                    x=np.arange(len(names)),
                    height=values,
                    width=0.6,
                    brush=pg.mkBrush(0, 120, 215)
                )
                self.cat_plot.addItem(bars)
                self.cat_plot.getAxis('bottom').setTicks([[(i, name[:15]) for i, name in enumerate(names)]])
                self.cat_plot.setXRange(-0.5, len(names) - 0.5)
                
        except Exception as e:
            print(f"⚠️ Categories table error: {e}")
    
    # ─── География ──────────────────────────────────────────────────────────
    
    def _build_geography(self, df):
        """Строит географию"""
        try:
            self.update_geography()
        except Exception as e:
            print(f"⚠️ Geography error: {e}")
    
    def update_geography(self):
        """Обновляет географию"""
        try:
            if self.filtered_data is None or len(self.filtered_data) == 0:
                return
            
            df = self.filtered_data
            geo_type = self.geo_type.currentText()
            
            if geo_type == "По ОМСУ":
                data = get_by_omsu(df)
                name_col = "ОМСУ"
            else:
                data = get_by_mro(df)
                name_col = "МРО"
            
            self.geo_table.setRowCount(len(data))
            for i, row in data.iterrows():
                self.geo_table.setItem(i, 0, QTableWidgetItem(str(row[name_col])))
                self.geo_table.setItem(i, 1, QTableWidgetItem(str(row["Всего"])))
                self.geo_table.setItem(i, 2, QTableWidgetItem(f"{row['Доля %']:.1f}%"))
                self.geo_table.setItem(i, 3, QTableWidgetItem(str(row.get("Выполнено", 0))))
                self.geo_table.setItem(i, 4, QTableWidgetItem(str(row.get("В работе", 0))))
                self.geo_table.setItem(i, 5, QTableWidgetItem(f"{row.get('Бэклог %', 0):.1f}%"))
            
            self.geo_plot.clear()
            if len(data) > 0:
                names = data[name_col].head(10).tolist()
                values = data["Всего"].head(10).tolist()
                
                bars = pg.BarGraphItem(
                    x=np.arange(len(names)),
                    height=values,
                    width=0.6,
                    brush=pg.mkBrush(0, 120, 215)
                )
                self.geo_plot.addItem(bars)
                self.geo_plot.getAxis('bottom').setTicks([[(i, name[:12]) for i, name in enumerate(names)]])
                self.geo_plot.setXRange(-0.5, len(names) - 0.5)
                self.geo_plot.setLabel('left', 'Количество')
                
        except Exception as e:
            print(f"⚠️ Update geography error: {e}")
    
    # ─── Аналитика "Мусор" ──────────────────────────────────────────────────
    
    def _build_trash(self, df):
        """Строит аналитику по мусору"""
        try:
            top_count, top_backlog = get_trash_analysis(df)
            
            self.trash_count_table.setRowCount(len(top_count))
            for i, row in top_count.iterrows():
                self.trash_count_table.setItem(i, 0, QTableWidgetItem(str(row["ОМСУ"])))
                self.trash_count_table.setItem(i, 1, QTableWidgetItem(str(row["Всего"])))
                self.trash_count_table.setItem(i, 2, QTableWidgetItem(f"{row['Доля %']:.1f}%"))
                self.trash_count_table.setItem(i, 3, QTableWidgetItem(str(row.get("Выполнено", 0))))
                self.trash_count_table.setItem(i, 4, QTableWidgetItem(str(row.get("В работе", 0))))
                self.trash_count_table.setItem(i, 5, QTableWidgetItem(f"{row.get('Бэклог %', 0):.1f}%"))
            
            self.trash_backlog_table.setRowCount(len(top_backlog))
            for i, row in top_backlog.iterrows():
                self.trash_backlog_table.setItem(i, 0, QTableWidgetItem(str(row["ОМСУ"])))
                self.trash_backlog_table.setItem(i, 1, QTableWidgetItem(str(row["Всего"])))
                self.trash_backlog_table.setItem(i, 2, QTableWidgetItem(f"{row['Доля %']:.1f}%"))
                self.trash_backlog_table.setItem(i, 3, QTableWidgetItem(str(row.get("Выполнено", 0))))
                self.trash_backlog_table.setItem(i, 4, QTableWidgetItem(str(row.get("В работе", 0))))
                self.trash_backlog_table.setItem(i, 5, QTableWidgetItem(f"{row.get('Бэклог %', 0):.1f}%"))
            
            self.trash_plot.clear()
            if len(top_count) > 0:
                names = top_count["ОМСУ"].head(10).tolist()
                values = top_count["Всего"].head(10).tolist()
                bars = pg.BarGraphItem(
                    x=np.arange(len(names)),
                    height=values,
                    width=0.6,
                    brush=pg.mkBrush(220, 53, 69)
                )
                self.trash_plot.addItem(bars)
                self.trash_plot.getAxis('bottom').setTicks([[(i, name[:12]) for i, name in enumerate(names)]])
                self.trash_plot.setXRange(-0.5, len(names) - 0.5)
                self.trash_plot.setLabel('left', 'Количество')
                self.trash_plot.setTitle('Топ ОМСУ по обращениям "Мусор, свалки, стоки"')
                
        except Exception as e:
            print(f"⚠️ Trash analysis error: {e}")
    
    # ─── ЭКСПОРТ ──────────────────────────────────────────────────────────
    
    def export_report(self):
        """Экспортирует отчёт"""
        try:
            if self.filtered_data is None or len(self.filtered_data) == 0:
                return
            
            path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить отчёт", "eco_report.xlsx", "Excel (*.xlsx)"
            )
            if not path:
                return
            
            self.filtered_data.to_excel(path, index=False)
            QMessageBox.information(self, "Успех", f"Отчёт сохранён:\n{path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить отчёт:\n{str(e)}")
    
    def go_back(self):
        """Возвращает на стартовый экран"""
        self.back_clicked.emit()