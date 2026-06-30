# logger.py
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path

# Настройка цветов для консоли (Windows)
class ColoredFormatter(logging.Formatter):
    """Форматтер с цветами для консоли"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Голубой
        'INFO': '\033[32m',       # Зеленый
        'WARNING': '\033[33m',    # Желтый
        'ERROR': '\033[31m',      # Красный
        'CRITICAL': '\033[35m',   # Фиолетовый
        'RESET': '\033[0m'        # Сброс
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logger(name: str = "EcoBI", log_file: str = "eco_bi.log") -> logging.Logger:
    """
    Настройка логгера с выводом в консоль и файл
    
    Args:
        name: Имя логгера
        log_file: Путь к файлу лога
    
    Returns:
        Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Очищаем старые обработчики
    logger.handlers.clear()
    
    # Формат сообщения
    formatter = ColoredFormatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s() | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 1. Консольный обработчик (все уровни)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 2. Файловый обработчик (подробный)
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s() | %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Не удалось создать файл лога: {e}")
    
    return logger


# Создаем глобальный логгер для всего приложения
logger = setup_logger()


def log_exception(logger: logging.Logger, e: Exception, context: str = ""):
    """Логирование исключения с полным traceback"""
    logger.error(f"❌ {context}: {str(e)}")
    logger.debug(f"Traceback:\n{traceback.format_exc()}")


def log_function_call(logger: logging.Logger):
    """Декоратор для логирования вызова функций"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"→ Вызов {func.__name__}()")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"← {func.__name__}() завершён")
                return result
            except Exception as e:
                logger.error(f"✖ {func.__name__}() ошибка: {e}")
                raise
        return wrapper
    return decorator


class LoggerMixin:
    """Миксин для добавления логгера в классы"""
    
    @property
    def log(self):
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(f"{self.__class__.__name__}")
        return self._logger
    
    def log_info(self, msg):
        self.log.info(msg)
    
    def log_debug(self, msg):
        self.log.debug(msg)
    
    def log_warning(self, msg):
        self.log.warning(msg)
    
    def log_error(self, msg, e=None):
        if e:
            self.log.error(f"{msg}: {e}")
            self.log.debug(traceback.format_exc())
        else:
            self.log.error(msg)