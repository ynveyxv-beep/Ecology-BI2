# test_two_plots.py - Тест с двумя графиками
import sys
import pyqtgraph as pg
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QFileDialog, QLabel, QTabWidget
)
import pandas as pd
import numpy as np
import os


class TestTwoPlots(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тест с двумя графиками")
        self.resize(1000, 700)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Кнопка
        self.load_btn = QPushButton("📂 Загрузить данные")
        self.load_btn.clicked.connect(self.load_data)
        layout.addWidget(self.load_btn)
        
        self.info_label = QLabel("Данные не загружены")
        layout.addWidget(self.info_label)
        
        # Вкладки
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Вкладка 1 - с одним графиком
        tab1 = QWidget()
        layout1 = QVBoxLayout(tab1)
        self.plot1 = pg.PlotWidget()
        self.plot1.setBackground('white')
        self.plot1.setLabel('left', 'Количество')
        self.plot1.setLabel('bottom', 'Категория')
        layout1.addWidget(self.plot1)
        self.tabs.addTab(tab1, "График 1")
        
        # Вкладка 2 - с двумя графиками
        tab2 = QWidget()
        layout2 = QVBoxLayout(tab2)
        
        self.plot2a = pg.PlotWidget()
        self.plot2a.setBackground('white')
        self.plot2a.setMinimumHeight(200)
        layout2.addWidget(self.plot2a)
        
        self.plot2b = pg.PlotWidget()
        self.plot2b.setBackground('white')
        self.plot2b.setMinimumHeight(200)
        layout2.addWidget(self.plot2b)
        
        self.tabs.addTab(tab2, "График 2")
        
        # Приветствие
        text = pg.TextItem("🌿 Загрузите данные", color=(150, 150, 150))
        text.setPos(0, 0)
        self.plot1.addItem(text)
        self.plot2a.addItem(text)
        self.plot2b.addItem(text)
        
        self.data = None
    
    def load_data(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Загрузить данные", "", "Excel (*.xlsx *.xls);;CSV (*.csv)"
        )
        
        if not path:
            return
        
        try:
            print(f"📄 Загрузка: {path}")
            df = pd.read_excel(path, engine='openpyxl')
            
            print(f"✅ Прочитано: {len(df)} строк")
            
            # Нормализация
            df.columns = [str(col).strip().lower() for col in df.columns]
            
            if 'date' not in df.columns:
                print("❌ Нет колонки date")
                return
            
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date'])
            
            self.data = df
            self.info_label.setText(f"✅ {len(df)} строк")
            
            self.build_charts()
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
    
    def build_charts(self):
        try:
            print("📊 Построение графиков...")
            
            # Очищаем
            self.plot1.clear()
            self.plot2a.clear()
            self.plot2b.clear()
            
            # Данные для графика 1 (категории)
            if 'category' in self.data.columns:
                counts = self.data['category'].value_counts().head(10)
                if len(counts) > 0:
                    bars = pg.BarGraphItem(
                        x=np.arange(len(counts)),
                        height=counts.values,
                        width=0.6,
                        brush=pg.mkBrush(0, 120, 215)
                    )
                    self.plot1.addItem(bars)
                    ticks = [[(i, str(name)[:15]) for i, name in enumerate(counts.index)]]
                    self.plot1.getAxis('bottom').setTicks(ticks)
                    self.plot1.setXRange(-0.5, len(counts) - 0.5)
                    self.plot1.setLabel('left', 'Количество')
                    self.plot1.setLabel('bottom', 'Категория')
            
            # Данные для графика 2a (временной ряд)
            df_copy = self.data.copy()
            df_copy['date_day'] = df_copy['date'].dt.date
            daily_counts = df_copy.groupby('date_day').size()
            daily_counts = daily_counts.sort_index()
            
            if len(daily_counts) > 0:
                x = np.arange(len(daily_counts))
                y = daily_counts.values
                
                self.plot2a.plot(
                    x, y,
                    pen=pg.mkPen(color=(40, 167, 69), width=2),
                    symbol='o',
                    symbolSize=4,
                    symbolBrush=(40, 167, 69)
                )
                self.plot2a.setLabel('left', 'Количество')
                self.plot2a.setLabel('bottom', 'Дни')
                self.plot2a.autoRange()
            
            # Данные для графика 2b (ещё один временной ряд)
            if 'status' in self.data.columns:
                df_status = self.data[self.data['status'] == 'выполнено'].copy()
                if len(df_status) > 0:
                    df_status['date_day'] = df_status['date'].dt.date
                    status_counts = df_status.groupby('date_day').size()
                    status_counts = status_counts.sort_index()
                    
                    if len(status_counts) > 0:
                        x = np.arange(len(status_counts))
                        y = status_counts.values
                        
                        self.plot2b.plot(
                            x, y,
                            pen=pg.mkPen(color=(255, 0, 0), width=2),
                            symbol='o',
                            symbolSize=4,
                            symbolBrush=(255, 0, 0)
                        )
                        self.plot2b.setLabel('left', 'Количество')
                        self.plot2b.setLabel('bottom', 'Дни')
                        self.plot2b.autoRange()
            
            print("✅ Графики построены")
            
        except Exception as e:
            print(f"❌ Ошибка построения: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestTwoPlots()
    window.show()
    sys.exit(app.exec())