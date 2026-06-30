# ui/eco_dashboard_window.py - МИНИМАЛЬНАЯ ВЕРСИЯ (только 2 графика)
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox,
    QTabWidget
)

import pandas as pd
import numpy as np
import pyqtgraph as pg
import traceback
import os

from logger import logger, LoggerMixin


class EcoDashboardWindow(QWidget, LoggerMixin):
    """Экологический дашборд - МИНИМАЛЬНАЯ ВЕРСИЯ (только 2 графика)"""
    
    back_clicked = Signal()
    
    def __init__(self):
        super().__init__()
        self.log.info("🚀 Инициализация EcoDashboardWindow (МИНИМАЛЬНАЯ)")
        
        self.data = None
        self.filtered_data = None
        self._is_building = False
        
        self.init_ui()
        self.show_welcome()
        
        self.log.info("✅ EcoDashboardWindow инициализирован")
    
    def init_ui(self):
        """Инициализация интерфейса - МИНИМАЛЬНАЯ"""
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
        
        # Только одна вкладка с двумя графиками
        self.tab_main = QWidget()
        self.tabs.addTab(self.tab_main, "📊 Дашборд")
        
        main_layout.addWidget(self.tabs)
        
        # ─── Создаём графики ──────────────────────────────────────────────
        layout = QVBoxLayout(self.tab_main)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # График 1: Временной ряд
        ts_label = QLabel("📈 Динамика обращений")
        ts_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(ts_label)
        
        self.ts_plot = pg.PlotWidget()
        self.ts_plot.setBackground('white')
        self.ts_plot.setMinimumHeight(250)
        self.ts_plot.setLabel('left', 'Количество')
        self.ts_plot.setLabel('bottom', 'Дни')
        layout.addWidget(self.ts_plot)
        
        # Разделитель
        line = QWidget()
        line.setFixedHeight(2)
        line.setStyleSheet("background: #dee2e6;")
        layout.addWidget(line)
        
        # График 2: Топ категорий
        cat_label = QLabel("🏆 Топ категорий")
        cat_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(cat_label)
        
        self.plot = pg.PlotWidget()
        self.plot.setBackground('white')
        self.plot.setMinimumHeight(250)
        self.plot.setLabel('left', 'Количество')
        self.plot.setLabel('bottom', 'Категория')
        layout.addWidget(self.plot)
    
    def show_welcome(self):
        """Показывает приветствие"""
        self.ts_plot.clear()
        self.plot.clear()
        
        text1 = pg.TextItem("🌿 Загрузите данные", color=(150, 150, 150))
        text1.setPos(0, 0)
        self.ts_plot.addItem(text1)
        
        text2 = pg.TextItem("🌿 Загрузите данные", color=(150, 150, 150))
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
            
            # Обработка дат
            if 'date' in df.columns:
                try:
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                    valid_dates = df['date'].notna().sum()
                    self.log.info(f"📅 Валидных дат: {valid_dates} из {len(df)}")
                except Exception as e:
                    self.log.warning(f"Ошибка дат: {e}")
            
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
            
            # ─── График 1: Временной ряд ──────────────────────────────────
            self._build_time_series(df)
            
            # ─── График 2: Топ категорий ──────────────────────────────────
            self._build_category_chart(df)
            
            self.log.info("✅ Дашборд построен")
            
        except Exception as e:
            self.log.critical(f"❌ Ошибка построения: {e}")
            self.log.critical(traceback.format_exc())
            QMessageBox.warning(self, "Ошибка", f"Не удалось построить дашборд:\n{str(e)}")
        
        finally:
            self._is_building = False
    
    def _build_time_series(self, df):
        """Строит временной ряд"""
        self.log.debug("→ _build_time_series()")
        
        try:
            self.ts_plot.clear()
            
            if 'date' not in df.columns:
                self.log.warning("⚠️ Нет колонки date")
                text = pg.TextItem("Нет данных с датой", color=(150, 150, 150))
                self.ts_plot.addItem(text)
                return
            
            df_copy = df.copy()
            df_copy['date'] = pd.to_datetime(df_copy['date'], errors='coerce')
            df_copy = df_copy.dropna(subset=['date'])
            
            if len(df_copy) == 0:
                self.log.warning("⚠️ Нет валидных дат")
                text = pg.TextItem("Нет валидных дат", color=(150, 150, 150))
                self.ts_plot.addItem(text)
                return
            
            df_copy['date_day'] = df_copy['date'].dt.date
            daily_counts = df_copy.groupby('date_day').size()
            daily_counts = daily_counts.sort_index()
            
            if len(daily_counts) == 0:
                self.log.warning("⚠️ Нет данных после группировки")
                text = pg.TextItem("Нет данных", color=(150, 150, 150))
                self.ts_plot.addItem(text)
                return
            
            x = np.arange(len(daily_counts))
            y = daily_counts.values
            
            self.ts_plot.plot(
                x, y,
                pen=pg.mkPen(color=(40, 167, 69), width=2),
                symbol='o',
                symbolSize=4,
                symbolBrush=(40, 167, 69)
            )
            
            self.ts_plot.setLabel('left', 'Количество')
            self.ts_plot.setLabel('bottom', 'Дни')
            self.ts_plot.autoRange()
            
            self.log.info("✅ Временной ряд построен")
            
        except Exception as e:
            self.log.error(f"⚠️ Ошибка временного ряда: {e}")
            traceback.print_exc()
            text = pg.TextItem(f"Ошибка: {str(e)[:30]}", color=(200, 50, 50))
            self.ts_plot.addItem(text)
    
    def _build_category_chart(self, df):
        """Строит график категорий"""
        self.log.debug("→ _build_category_chart()")
        
        try:
            self.plot.clear()
            
            if 'category' not in df.columns:
                self.log.warning("⚠️ Нет колонки category")
                text = pg.TextItem("Нет данных", color=(150, 150, 150))
                self.plot.addItem(text)
                return
            
            counts = df['category'].value_counts().head(10)
            
            if len(counts) == 0:
                self.log.warning("⚠️ Нет категорий")
                text = pg.TextItem("Нет данных", color=(150, 150, 150))
                self.plot.addItem(text)
                return
            
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
            
        except Exception as e:
            self.log.error(f"⚠️ Ошибка графика категорий: {e}")
            traceback.print_exc()
            text = pg.TextItem(f"Ошибка: {str(e)[:30]}", color=(200, 50, 50))
            self.plot.addItem(text)
    
    def go_back(self):
        self.log.info("⬅️ Возврат")
        self.back_clicked.emit()