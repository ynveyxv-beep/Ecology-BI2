"""
DataManager — управление загрузкой и хранением данных.
Дополнен поддержкой экологических данных через eco_modules.
"""

import pandas as pd
from typing import Optional, Dict, Any, Tuple
from pathlib import Path


class DataManager:
    """Управление загрузкой и хранением данных"""
    
    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.file_path: Optional[str] = None
        self._eco_report: Optional[Dict] = None
        self._is_eco_data: bool = False
    
    def load_file(self, path: str) -> pd.DataFrame:
        """
        Загружает файл данных.
        Поддерживает CSV, XLSX (с авто-определением формата).
        """
        self.file_path = path
        ext = Path(path).suffix.lower()
        
        if ext in ['.xlsx', '.xls']:
            return self._load_excel(path)
        elif ext == '.csv':
            return self._load_csv(path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def _load_csv(self, path: str) -> pd.DataFrame:
        """Загружает CSV файл"""
        self.df = pd.read_csv(path)
        self._is_eco_data = False
        self._eco_report = None
        return self.df
    
    def _load_excel(self, path: str) -> pd.DataFrame:
        """
        Загружает Excel файл.
        Пытается использовать eco_modules.load_excel для экологических данных.
        Если не получается — загружает стандартным способом.
        """
        try:
            from eco_modules import load_excel
            df, report = load_excel(path)
            self.df = df
            self._eco_report = report
            self._is_eco_data = True
            return df
        except Exception as e:
            # Если не получилось загрузить как экоданные — пробуем стандартно
            print(f"⚠️ Eco-loader failed: {e}. Trying standard load...")
            self.df = pd.read_excel(path)
            self._is_eco_data = False
            self._eco_report = None
            return self.df
    
    def get_eco_report(self) -> Optional[Dict]:
        """Возвращает отчёт о загрузке экоданных"""
        return self._eco_report
    
    def is_eco_data(self) -> bool:
        """Проверяет, являются ли данные экологическими"""
        return self._is_eco_data
    
    def get_data(self) -> Optional[pd.DataFrame]:
        """Возвращает данные"""
        return self.df
    
    def get_columns(self) -> list:
        """Возвращает список колонок"""
        if self.df is None:
            return []
        return list(self.df.columns)
    
    def get_row_count(self) -> int:
        """Возвращает количество строк"""
        if self.df is None:
            return 0
        return len(self.df)
    
    def get_column_names(self) -> list:
        """Возвращает имена колонок (алиас)"""
        return self.get_columns()