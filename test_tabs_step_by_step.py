# test_tabs_step_by_step.py - Пошаговый тест каждой вкладки
import sys
import pandas as pd
import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
import os
import traceback

from eco_modules import (
    get_kpi, get_by_category, get_by_omsu, get_by_mro,
    get_time_series, get_trash_analysis
)


class TestTabsStepByStep(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тест вкладок - пошагово")
        self.resize(1200, 800)
        
        self.data = None
        self.filtered_data = None
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Кнопка загрузки
        self.load_btn = QPushButton("📂 Загрузить данные")
        self.load_btn.clicked.connect(self.load_data)
        layout.addWidget(self.load_btn)
        
        self.info_label = QLabel("Данные не загружены")
        layout.addWidget(self.info_label)
        
        # Кнопки для пошагового построения
        btn_layout = QHBoxLayout()
        
        btn1 = QPushButton("1. Построить Обзор")
        btn1.clicked.connect(self.build_overview_only)
        btn_layout.addWidget(btn1)
        
        btn2 = QPushButton("2. Построить Категории")
        btn2.clicked.connect(self.build_categories_only)
        btn_layout.addWidget(btn2)
        
        btn3 = QPushButton("3. Построить Географию")
        btn3.clicked.connect(self.build_geography_only)
        btn_layout.addWidget(btn3)
        
        btn4 = QPushButton("4. Построить Мусор")
        btn4.clicked.connect(self.build_trash_only)
        btn_layout.addWidget(btn4)
        
        layout.addLayout(btn_layout)
        
        # Вкладки
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Создаём вкладки
        self.tab_overview = QWidget()
        self.tab_categories = QWidget()
        self.tab_geography = QWidget()
        self.tab_trash = QWidget()
        
        self.tabs.addTab(self.tab_overview, "📊 Обзор")
        self.tabs.addTab(self.tab_categories, "📋 Категории")
        self.tabs.addTab(self.tab_geography, "🗺️ География")
        self.tabs.addTab(self.tab_trash, "♻️ Мусор")
        
        # Создаём виджеты для каждой вкладки
        self._create_overview()
        self._create_categories()
        self._create_geography()
        self._create_trash()
    
    def _create_overview(self):
        layout = QVBoxLayout(self.tab_overview)
        layout.setContentsMargins(10, 10, 10, 10)
        self.ts_plot = pg.PlotWidget()
        self.ts_plot.setBackground('white')
        self.ts_plot.setMinimumHeight(200)
        layout.addWidget(self.ts_plot)
        self.cat_plot = pg.PlotWidget()
        self.cat_plot.setBackground('white')
        self.cat_plot.setMinimumHeight(200)
        layout.addWidget(self.cat_plot)
    
    def _create_categories(self):
        layout = QVBoxLayout(self.tab_categories)
        layout.setContentsMargins(10, 10, 10, 10)
        self.cat_table = QTableWidget()
        self.cat_table.setColumnCount(5)
        self.cat_table.setHorizontalHeaderLabels(["Категория", "Всего", "Доля %", "Выполнено", "В работе"])
        self.cat_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.cat_table)
        self.cat_plot2 = pg.PlotWidget()
        self.cat_plot2.setBackground('white')
        self.cat_plot2.setMinimumHeight(200)
        layout.addWidget(self.cat_plot2)
    
    def _create_geography(self):
        layout = QVBoxLayout(self.tab_geography)
        layout.setContentsMargins(10, 10, 10, 10)
        switch = QHBoxLayout()
        switch.addWidget(QLabel("Показать:"))
        self.geo_type = QComboBox()
        self.geo_type.addItems(["По ОМСУ", "По МРО"])
        self.geo_type.currentTextChanged.connect(self.update_geography)
        switch.addWidget(self.geo_type)
        switch.addStretch()
        layout.addLayout(switch)
        self.geo_table = QTableWidget()
        self.geo_table.setColumnCount(6)
        self.geo_table.setHorizontalHeaderLabels(["Наименование", "Всего", "Доля %", "Выполнено", "В работе", "Бэклог %"])
        self.geo_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.geo_table)
        self.geo_plot = pg.PlotWidget()
        self.geo_plot.setBackground('white')
        self.geo_plot.setMinimumHeight(200)
        layout.addWidget(self.geo_plot)
    
    def _create_trash(self):
        layout = QVBoxLayout(self.tab_trash)
        layout.setContentsMargins(10, 10, 10, 10)
        row = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(QLabel("🏆 Топ по числу обращений"))
        self.trash_count_table = QTableWidget()
        self.trash_count_table.setColumnCount(6)
        self.trash_count_table.setHorizontalHeaderLabels(["ОМСУ", "Всего", "Доля %", "Выполнено", "В работе", "Бэклог %"])
        self.trash_count_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        left.addWidget(self.trash_count_table)
        row.addLayout(left, 1)
        right = QVBoxLayout()
        right.addWidget(QLabel("🏆 Топ по бэклогу"))
        self.trash_backlog_table = QTableWidget()
        self.trash_backlog_table.setColumnCount(6)
        self.trash_backlog_table.setHorizontalHeaderLabels(["ОМСУ", "Всего", "Доля %", "Выполнено", "В работе", "Бэклог %"])
        self.trash_backlog_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right.addWidget(self.trash_backlog_table)
        row.addLayout(right, 1)
        layout.addLayout(row)
        self.trash_plot = pg.PlotWidget()
        self.trash_plot.setBackground('white')
        self.trash_plot.setMinimumHeight(200)
        layout.addWidget(self.trash_plot)
    
    def load_data(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Загрузить данные", "", "Excel (*.xlsx *.xls);;CSV (*.csv)"
        )
        if not path:
            return
        try:
            print(f"📄 Загрузка: {path}")
            if path.endswith('.csv'):
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path, engine='openpyxl')
            print(f"✅ Прочитано: {len(df)} строк")
            df.columns = [str(col).strip().lower() for col in df.columns]
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
                    else x
                )
            self.data = df
            self.filtered_data = df.copy()
            self.info_label.setText(f"✅ {len(df)} строк")
            print("✅ Данные загружены и нормализованы")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def build_overview_only(self):
        """Только вкладка Обзор"""
        print("\n" + "="*60)
        print("📊 ПОСТРОЕНИЕ ТОЛЬКО ОБЗОРА")
        print("="*60)
        
        try:
            df = self.filtered_data
            if df is None or len(df) == 0:
                print("❌ Нет данных")
                return
            
            print("1. Временной ряд...")
            self.ts_plot.clear()
            ts = get_time_series(df, freq='D')
            print(f"   Временной ряд: {len(ts)} точек")
            
            if len(ts) > 0:
                dates = ts['Дата'].dt.strftime('%d.%m')
                if 'Выполнено' in ts.columns:
                    self.ts_plot.plot(dates, ts['Выполнено'].values, pen=pg.mkPen(color=(40, 167, 69), width=2), name='Выполнено')
                if 'В работе' in ts.columns:
                    self.ts_plot.plot(dates, ts['В работе'].values, pen=pg.mkPen(color=(253, 126, 20), width=2), name='В работе')
                self.ts_plot.addLegend()
                self.ts_plot.autoRange()
                print("   ✅ Временной ряд построен")
            
            print("2. Топ категорий...")
            self.cat_plot.clear()
            cat = get_by_category(df)
            print(f"   Категорий: {len(cat)}")
            
            if len(cat) > 0:
                top = cat.head(10)
                bars = pg.BarGraphItem(
                    x=np.arange(len(top)),
                    height=top['Всего'].values,
                    width=0.6,
                    brush=pg.mkBrush(0, 120, 215)
                )
                self.cat_plot.addItem(bars)
                ticks = [[(i, str(name)[:15]) for i, name in enumerate(top['Категория'].values)]]
                self.cat_plot.getAxis('bottom').setTicks(ticks)
                self.cat_plot.setXRange(-0.5, len(top) - 0.5)
                print("   ✅ Топ категорий построен")
            
            print("✅ ОБЗОР ГОТОВ")
            
        except Exception as e:
            print(f"❌ ОШИБКА: {e}")
            traceback.print_exc()
    
    def build_categories_only(self):
        """Только вкладка Категории"""
        print("\n" + "="*60)
        print("📋 ПОСТРОЕНИЕ ТОЛЬКО КАТЕГОРИЙ")
        print("="*60)
        
        try:
            df = self.filtered_data
            if df is None or len(df) == 0:
                print("❌ Нет данных")
                return
            
            print("1. Получение данных...")
            cat = get_by_category(df)
            print(f"   Категорий: {len(cat)}")
            
            print("2. Заполнение таблицы...")
            self.cat_table.setRowCount(len(cat))
            for i, row in cat.iterrows():
                self.cat_table.setItem(i, 0, QTableWidgetItem(str(row['Категория'])))
                self.cat_table.setItem(i, 1, QTableWidgetItem(str(row['Всего'])))
                self.cat_table.setItem(i, 2, QTableWidgetItem(f"{row['Доля %']:.1f}%"))
                self.cat_table.setItem(i, 3, QTableWidgetItem(str(row.get('Выполнено', 0))))
                self.cat_table.setItem(i, 4, QTableWidgetItem(str(row.get('В работе', 0))))
            print("   ✅ Таблица заполнена")
            
            print("3. Построение графика...")
            self.cat_plot2.clear()
            if len(cat) > 0:
                bars = pg.BarGraphItem(
                    x=np.arange(len(cat)),
                    height=cat['Всего'].values,
                    width=0.6,
                    brush=pg.mkBrush(0, 120, 215)
                )
                self.cat_plot2.addItem(bars)
                ticks = [[(i, str(name)[:15]) for i, name in enumerate(cat['Категория'].values)]]
                self.cat_plot2.getAxis('bottom').setTicks(ticks)
                self.cat_plot2.setXRange(-0.5, len(cat) - 0.5)
                print("   ✅ График построен")
            
            print("✅ КАТЕГОРИИ ГОТОВЫ")
            
        except Exception as e:
            print(f"❌ ОШИБКА: {e}")
            traceback.print_exc()
    
    def build_geography_only(self):
        """Только вкладка География"""
        print("\n" + "="*60)
        print("🗺️ ПОСТРОЕНИЕ ТОЛЬКО ГЕОГРАФИИ")
        print("="*60)
        
        try:
            df = self.filtered_data
            if df is None or len(df) == 0:
                print("❌ Нет данных")
                return
            
            print("1. Получение данных по ОМСУ...")
            omsu = get_by_omsu(df)
            print(f"   ОМСУ: {len(omsu)}")
            
            print("2. Заполнение таблицы...")
            self.geo_table.setRowCount(len(omsu))
            for i, row in omsu.iterrows():
                self.geo_table.setItem(i, 0, QTableWidgetItem(str(row['ОМСУ'])))
                self.geo_table.setItem(i, 1, QTableWidgetItem(str(row['Всего'])))
                self.geo_table.setItem(i, 2, QTableWidgetItem(f"{row['Доля %']:.1f}%"))
                self.geo_table.setItem(i, 3, QTableWidgetItem(str(row.get('Выполнено', 0))))
                self.geo_table.setItem(i, 4, QTableWidgetItem(str(row.get('В работе', 0))))
                self.geo_table.setItem(i, 5, QTableWidgetItem(f"{row.get('Бэклог %', 0):.1f}%"))
            print("   ✅ Таблица заполнена")
            
            print("3. Построение графика...")
            self.geo_plot.clear()
            if len(omsu) > 0:
                top = omsu.head(10)
                bars = pg.BarGraphItem(
                    x=np.arange(len(top)),
                    height=top['Всего'].values,
                    width=0.6,
                    brush=pg.mkBrush(0, 120, 215)
                )
                self.geo_plot.addItem(bars)
                ticks = [[(i, str(name)[:12]) for i, name in enumerate(top['ОМСУ'].values)]]
                self.geo_plot.getAxis('bottom').setTicks(ticks)
                self.geo_plot.setXRange(-0.5, len(top) - 0.5)
                print("   ✅ График построен")
            
            print("✅ ГЕОГРАФИЯ ГОТОВА")
            
        except Exception as e:
            print(f"❌ ОШИБКА: {e}")
            traceback.print_exc()
    
    def build_trash_only(self):
        """Только вкладка Мусор"""
        print("\n" + "="*60)
        print("♻️ ПОСТРОЕНИЕ ТОЛЬКО МУСОРА")
        print("="*60)
        
        try:
            df = self.filtered_data
            if df is None or len(df) == 0:
                print("❌ Нет данных")
                return
            
            print("1. Получение данных...")
            top_count, top_backlog = get_trash_analysis(df)
            print(f"   Мусор (count): {len(top_count)}, (backlog): {len(top_backlog)}")
            
            print("2. Заполнение таблиц...")
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
                self.trash_backlog_table.setItem(i, 4, QTableWidgetItem(str(row.get('В работе', 0))))
                self.trash_backlog_table.setItem(i, 5, QTableWidgetItem(f"{row.get('Бэклог %', 0):.1f}%"))
            print("   ✅ Таблицы заполнены")
            
            print("3. Построение графика...")
            self.trash_plot.clear()
            if len(top_count) > 0:
                top10 = top_count.head(10)
                bars = pg.BarGraphItem(
                    x=np.arange(len(top10)),
                    height=top10['Всего'].values,
                    width=0.6,
                    brush=pg.mkBrush(220, 53, 69)
                )
                self.trash_plot.addItem(bars)
                ticks = [[(i, str(name)[:12]) for i, name in enumerate(top10['ОМСУ'].values)]]
                self.trash_plot.getAxis('bottom').setTicks(ticks)
                self.trash_plot.setXRange(-0.5, len(top10) - 0.5)
                print("   ✅ График построен")
            
            print("✅ МУСОР ГОТОВ")
            
        except Exception as e:
            print(f"❌ ОШИБКА: {e}")
            traceback.print_exc()
    
    def update_geography(self):
        if self.filtered_data is not None:
            self.build_geography_only()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestTabsStepByStep()
    window.show()
    sys.exit(app.exec())