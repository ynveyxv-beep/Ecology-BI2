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
        from app import MainWindow
        
        logger.info("Создание QApplication...")
        app = QApplication(sys.argv)
        
        logger.info("Создание MainWindow...")
        window = MainWindow()
        window.show()
        
        logger.info("Запуск event loop...")
        sys.exit(app.exec())
        
    except Exception as e:
        logger.critical(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        logger.critical(traceback.format_exc())
        input("Нажмите Enter для выхода...")

if __name__ == '__main__':
    main()