# ui/eco_dashboard_window.py - ПРОСТАЯ ВЕРСИЯ ВРЕМЕННОГО РЯДА
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QGridLayout, QComboBox
)

import pandas as pd
import numpy as np
import pyqtgraph as pg
import traceback
import os

from logger import logger, LoggerMixin


class EcoDashboardWindow(QWidget, LoggerMixin):
    """Экологический дашборд - ПРОСТАЯ ВЕРСИЯ"""
    
    back_clicked = Signal()
    
    def __init__(self):
        super().__init__()
        self.log.info("🚀 Инициализация EcoDashboardWindow")
        
        self.data = None
        self.filtered_data = None
        self._is_building = False
        
        self.init_ui()
        self.show_welcome()
        
        self.log.info("✅ EcoDashboardWindow инициализирован")
    
    def init_ui(self):
        """Инициализация интерфейса"""
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
        
        toolbar_layout.addStretch()
        
        self.info_label = QLabel("Данные не загружены")
        self.info_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        toolbar_layout.addWidget(self.info_label)
        
        main_layout.addWidget(toolbar)
        
        # ─── Вкладки ──────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: #f5f5f5; }
            QTabBar::tab { padding: 8px 16px; background: #e9ecef; border: none; }
            QTabBar::tab:selected { background: white; font-weight: bold; }
        """)
        
        self.tab_overview = QWidget()
        self.tab_categories = QWidget()
        
        self.tabs.addTab(self.tab_overview, "📊 Обзор")
        self.tabs.addTab(self.tab_categories, "📋 Данные")
        
        main_layout.addWidget(self.tabs)
        
        # Создаём виджеты
        self._create_overview_widgets()
        self._create_categories_widgets()
    
    def _create_overview_widgets(self):
        """Создаёт виджеты для вкладки Обзор"""
        layout = QVBoxLayout(self.tab_overview)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # ─── KPI-карточки ────────────────────────────────────────────────
        self.kpi_container = QWidget()
        self.kpi_layout = QGridLayout(self.kpi_container)
        self.kpi_layout.setSpacing(10)
        layout.addWidget(self.kpi_container)
        
        # Создаём 6 карточек
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
        
        # ─── Временной ряд (ПРОСТАЯ ВЕРСИЯ) ─────────────────────────────
        ts_container = QWidget()
        ts_layout = QVBoxLayout(ts_container)
        ts_layout.setContentsMargins(0, 0, 0, 0)
        ts_layout.setSpacing(5)
        
        ts_header = QHBoxLayout()
        ts_label = QLabel("📈 Динамика обращений")
        ts_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        ts_header.addWidget(ts_label)
        ts_header.addStretch()
        
        self.ts_freq = QComboBox()
        self.ts_freq.addItems(["По дням", "По неделям", "По месяцам"])
        self.ts_freq.currentTextChanged.connect(self.on_ts_freq_changed)
        ts_header.addWidget(QLabel("Группировка:"))
        ts_header.addWidget(self.ts_freq)
        
        ts_layout.addLayout(ts_header)
        
        # Используем обычный GraphicsView вместо PlotWidget для теста
        self.ts_plot = pg.PlotWidget()
        self.ts_plot.setBackground('white')
        self.ts_plot.setMinimumHeight(250)
        self.ts_plot.setLabel('left', 'Количество')
        self.ts_plot.setLabel('bottom', 'Дата')
        # НЕ добавляем легенду
        ts_layout.addWidget(self.ts_plot)
        
        layout.addWidget(ts_container)
        
        # ─── График категорий ────────────────────────────────────────────
        cat_container = QWidget()
        cat_layout = QVBoxLayout(cat_container)
        cat_layout.setContentsMargins(0, 0, 0, 0)
        
        cat_label = QLabel("🏆 Топ категорий")
        cat_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        cat_layout.addWidget(cat_label)
        
        self.plot = pg.PlotWidget()
        self.plot.setBackground('white')
        self.plot.setMinimumHeight(250)
        self.plot.setLabel('left', 'Количество')
        self.plot.setLabel('bottom', 'Категория')
        cat_layout.addWidget(self.plot)
        
        layout.addWidget(cat_container)
    
    def _create_categories_widgets(self):
        """Создаёт виджеты для вкладки Данные"""
        layout = QVBoxLayout(self.tab_categories)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Дата", "Статус", "Категория", "ОМСУ", "МРО"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
    
    def on_ts_freq_changed(self):
        """Обновляет временной ряд при смене частоты"""
        if self.filtered_data is not None and len(self.filtered_data) > 0:
            self._build_time_series_simple(self.filtered_data)
    
    def show_welcome(self):
        """Показывает приветствие"""
        for value_label, name_label in self.kpi_cards:
            value_label.setText("—")
        
        self.ts_plot.clear()
        self.plot.clear()
        
        text1 = pg.TextItem("🌿 Загрузите данные для отображения", color=(150, 150, 150))
        text1.setPos(0, 0)
        self.ts_plot.addItem(text1)
        
        text2 = pg.TextItem("🌿 Загрузите данные для отображения", color=(150, 150, 150))
        text2.setPos(0, 0)
        self.plot.addItem(text2)
        
        self.info_label.setText("Данные не загружены")
    
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
            
            # Нормализация
            df.columns = [str(col).strip().lower() for col in df.columns]
            
            # Добавляем недостающие колонки
            for col in ['date', 'status', 'category', 'omsu', 'mro']:
                if col not in df.columns:
                    df[col] = 'Не указано'
            
            # Обработка дат
            if 'date' in df.columns:
                try:
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                    valid_dates = df['date'].notna().sum()
                    self.log.info(f"📅 Валидных дат: {valid_dates} из {len(df)}")
                except Exception as e:
                    self.log.warning(f"Ошибка дат: {e}")
            
            # Обработка статусов
            if 'status' in df.columns:
                try:
                    df['status'] = df['status'].astype(str).str.lower().str.strip()
                except Exception as e:
                    self.log.warning(f"Ошибка статусов: {e}")
            
            self.data = df
            self.filtered_data = df.copy()
            
            self.log.info(f"✅ Данные загружены: {len(df)} строк")
            self.info_label.setText(f"✅ {len(df)} строк")
            
            self.build_dashboard()
            
        except Exception as e:
            self.log.critical(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            self.log.critical(traceback.format_exc())
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить:\n{str(e)}")
    
    def build_dashboard(self):
        """Строит дашборд"""
        self.log.info("🏗️ Построение дашборда")
        
        if self._is_building:
            return
        
        self._is_building = True
        
        try:
            df = self.filtered_data
            
            if df is None or len(df) == 0:
                self.show_welcome()
                return
            
            self.log.debug(f"Строим из {len(df)} строк")
            
            # ─── Обновляем KPI ────────────────────────────────────────────
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
            
            # ─── Временной ряд (ПРОСТАЯ ВЕРСИЯ) ──────────────────────────
            self._build_time_series_simple(df)
            
            # ─── График категорий ─────────────────────────────────────────
            self.plot.clear()
            
            if 'category' in df.columns:
                counts = df['category'].value_counts().head(10)
                
                if len(counts) > 0:
                    bars = pg.BarGraphItem(
                        x=np.arange(len(counts)),
                        height=counts.values,
                        width=0.6,
                        brush=pg.mkBrush(0, 120, 215)
                    )
                    self.plot.addItem(bars)
                    
                    ticks = [[(i, str(name)[:15]) for i, name in enumerate(counts.index)]]
                    self.plot.getAxis('bottom').setTicks(ticks)
                    self.plot.setXRange(-0.5, len(counts) - 0.5)
                    self.plot.setLabel('left', 'Количество')
                    self.plot.setLabel('bottom', 'Категория')
                    
                    self.log.info(f"✅ Построен график с {len(counts)} категориями")
            
            # ─── Заполняем таблицу ────────────────────────────────────────
            self.table.setRowCount(min(len(df), 100))
            for i in range(min(len(df), 100)):
                row = df.iloc[i]
                self.table.setItem(i, 0, QTableWidgetItem(str(row.get('date', ''))[:10]))
                self.table.setItem(i, 1, QTableWidgetItem(str(row.get('status', ''))))
                self.table.setItem(i, 2, QTableWidgetItem(str(row.get('category', ''))))
                self.table.setItem(i, 3, QTableWidgetItem(str(row.get('omsu', ''))))
                self.table.setItem(i, 4, QTableWidgetItem(str(row.get('mro', ''))))
            
            self.log.info("✅ Дашборд построен")
            
        except Exception as e:
            self.log.critical(f"❌ Ошибка построения: {e}")
            self.log.critical(traceback.format_exc())
            QMessageBox.warning(self, "Ошибка", f"Не удалось построить дашборд:\n{str(e)}")
        
        finally:
            self._is_building = False
    
    def _build_time_series_simple(self, df):
        """Строит временной ряд - ПРОСТАЯ ВЕРСИЯ (только одна линия)"""
        self.log.debug("→ _build_time_series_simple()")
        
        try:
            self.ts_plot.clear()
            
            # Проверяем наличие колонок
            if 'date' not in df.columns or 'status' not in df.columns:
                self.log.warning("⚠️ Нет колонок date или status")
                text = pg.TextItem("Нет данных", color=(150, 150, 150))
                self.ts_plot.addItem(text)
                return
            
            # Берём только выполненные
            df_copy = df[df['status'] == 'выполнено'].copy()
            
            if len(df_copy) == 0:
                self.log.warning("⚠️ Нет выполненных")
                text = pg.TextItem("Нет выполненных", color=(150, 150, 150))
                self.ts_plot.addItem(text)
                return
            
            # Конвертируем даты
            df_copy['date'] = pd.to_datetime(df_copy['date'], errors='coerce')
            df_copy = df_copy.dropna(subset=['date'])
            
            if len(df_copy) == 0:
                self.log.warning("⚠️ Нет валидных дат")
                text = pg.TextItem("Нет валидных дат", color=(150, 150, 150))
                self.ts_plot.addItem(text)
                return
            
            # Группируем по дням
            df_copy['date_day'] = df_copy['date'].dt.date
            daily_counts = df_copy.groupby('date_day').size()
            daily_counts = daily_counts.sort_index()
            
            if len(daily_counts) == 0:
                self.log.warning("⚠️ Нет данных после группировки")
                text = pg.TextItem("Нет данных", color=(150, 150, 150))
                self.ts_plot.addItem(text)
                return
            
            # Подготовка данных для графика
            x = np.arange(len(daily_counts))
            y = daily_counts.values
            
            # Рисуем линию
            self.ts_plot.plot(
                x, y,
                pen=pg.mkPen(color=(40, 167, 69), width=2),
                symbol='o',
                symbolSize=5,
                symbolBrush=(40, 167, 69)
            )
            
            # Настройки
            self.ts_plot.setLabel('left', 'Количество')
            self.ts_plot.setLabel('bottom', 'Дни')
            self.ts_plot.autoRange()
            
            self.log.info("✅ Простой временной ряд построен")
            
        except Exception as e:
            self.log.error(f"⚠️ Ошибка временного ряда: {e}")
            traceback.print_exc()
            text = pg.TextItem(f"Ошибка: {str(e)[:30]}", color=(200, 50, 50))
            self.ts_plot.addItem(text)
    
    def go_back(self):
        self.log.info("⬅️ Возврат")
        self.back_clicked.emit()