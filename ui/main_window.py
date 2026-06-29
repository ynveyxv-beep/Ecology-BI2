from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget
)

from ui.start_screen import StartScreen
from ui.eco_dashboard_window import EcoDashboardWindow
from ui.configurator_window import ConfiguratorWindow


class MainWindow(QMainWindow):
    """Главное окно приложения с переключением режимов"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Ecology-BI")
        self.resize(1400, 900)
        
        # Центральный виджет со стеком
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.stacked = QStackedWidget()
        layout.addWidget(self.stacked)
        
        # 1. Стартовый экран
        self.start_screen = StartScreen()
        self.start_screen.mode_selected.connect(self.switch_mode)
        self.stacked.addWidget(self.start_screen)
        
        # 2. Экологический дашборд
        self.eco_dashboard = EcoDashboardWindow()
        self.eco_dashboard.back_clicked.connect(self.show_start_screen)
        self.stacked.addWidget(self.eco_dashboard)
        
        # 3. Конфигуратор (ваш существующий ConfiguratorWindow)
        self.configurator = ConfiguratorWindow()
        self.configurator.setParent(self)
        self.stacked.addWidget(self.configurator)
        
        # Показываем стартовый экран
        self.stacked.setCurrentIndex(0)
    
    def switch_mode(self, mode: str):
        """Переключает режим работы"""
        if mode == 'eco':
            self.stacked.setCurrentIndex(1)  # Экодашборд
            self.setWindowTitle("Ecology-BI — Экологический дашборд")
        elif mode == 'configurator':
            self.stacked.setCurrentIndex(2)  # Конфигуратор
            self.setWindowTitle("Ecology-BI — Конфигуратор дашбордов")
    
    def show_start_screen(self):
        """Показывает стартовый экран"""
        self.stacked.setCurrentIndex(0)
        self.setWindowTitle("Ecology-BI")