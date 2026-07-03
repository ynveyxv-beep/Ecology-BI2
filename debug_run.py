# debug_run.py
import sys
import os
import logging
import traceback

# Настройка логирования
from logger import setup_logger, logger

def main():
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК ПРИЛОЖЕНИЯ В РЕЖИМЕ ОТЛАДКИ")
    logger.info("=" * 60)
    
    # Информация о системе
    logger.debug(f"Python: {sys.version}")
    logger.debug(f"Рабочая папка: {os.getcwd()}")
    logger.debug(f"Файлы в папке: {os.listdir('.')}")
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt

        logger.info("Создание QApplication...")
        app = QApplication(sys.argv)
        app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

        # Splash screen
        from ui.splash_screen import SplashScreen, LOAD_STEPS
        splash = SplashScreen()
        splash.show()
        splash.set_progress(LOAD_STEPS[0][1], LOAD_STEPS[0][0])

        from ui import theme  # noqa
        splash.set_progress(LOAD_STEPS[1][1], LOAD_STEPS[1][0])

        from ui.start_screen import StartScreen              # noqa
        from ui.eco_dashboard_window import EcoDashboardWindow  # noqa
        from ui.configurator_window import ConfiguratorWindow   # noqa
        splash.set_progress(LOAD_STEPS[2][1], LOAD_STEPS[2][0])

        logger.info("Создание MainWindow...")
        from ui.main_window import MainWindow
        splash.set_progress(LOAD_STEPS[3][1], LOAD_STEPS[3][0])
        window = MainWindow()

        splash.set_progress(LOAD_STEPS[4][1], LOAD_STEPS[4][0])
        splash.finish(window)

        logger.info("Запуск event loop...")
        sys.exit(app.exec())
        
    except Exception as e:
        logger.critical(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        logger.critical(traceback.format_exc())
        input("Нажмите Enter для выхода...")

if __name__ == '__main__':
    main()