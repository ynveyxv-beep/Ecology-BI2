# ui/main_window.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget
)

from ui.start_screen import StartScreen
from ui.eco_dashboard_window import EcoDashboardWindow
from ui.configurator_window import ConfiguratorWindow
from logger import logger


class MainWindow(QMainWindow):
    """Главное окно приложения с переключением режимов"""

    def __init__(self):
        logger.info("🚀 Запуск MainWindow")
        super().__init__()

        self.setWindowTitle("Ecology-BI")
        self.resize(1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stacked = QStackedWidget()
        layout.addWidget(self.stacked)

        # 1. Стартовый экран
        logger.debug("Создание StartScreen")
        self.start_screen = StartScreen()
        self.start_screen.mode_selected.connect(self.switch_mode)
        self.start_screen.template_selected.connect(self._on_template_selected)
        self.stacked.addWidget(self.start_screen)

        # 2. Экологический дашборд
        logger.debug("Создание EcoDashboardWindow")
        self.eco_dashboard = EcoDashboardWindow()
        self.eco_dashboard.back_clicked.connect(self.show_start_screen)
        self.stacked.addWidget(self.eco_dashboard)

        # 3. Конфигуратор
        logger.debug("Создание ConfiguratorWindow")
        self.configurator = ConfiguratorWindow()
        self.configurator.back_clicked.connect(self.show_start_screen)
        self.stacked.addWidget(self.configurator)

        self.stacked.setCurrentIndex(0)
        logger.info("✅ MainWindow инициализирован")

    def switch_mode(self, mode: str):
        logger.info(f"🔄 Переключение режима: {mode}")

        if mode == 'eco':
            self.stacked.setCurrentIndex(1)
            self.setWindowTitle("Ecology-BI — Экологический дашборд")
            logger.info("✅ Переключено на экологический дашборд")
        elif mode == 'configurator':
            # «Новый дашборд» — всегда начинаем с чистого листа
            self.configurator._new_dashboard()
            self.stacked.setCurrentIndex(2)
            self.setWindowTitle("Ecology-BI — Конфигуратор дашбордов")
            logger.info("✅ Переключено на конфигуратор (новый дашборд)")

    def _on_template_selected(self, action: str, path: str):
        """Обработчик выбора последнего дашборда на стартовом экране."""
        logger.info(f"📂 Открытие дашборда из стартового экрана: {path}")
        if action == 'load_template':
            self.stacked.setCurrentIndex(2)
            self.setWindowTitle("Ecology-BI — Конфигуратор дашбордов")
            self.configurator.load_dashboard_from_path(path)

    def show_start_screen(self):
        logger.debug("Возврат на стартовый экран")
        self.stacked.setCurrentIndex(0)
        self.setWindowTitle("Ecology-BI")
