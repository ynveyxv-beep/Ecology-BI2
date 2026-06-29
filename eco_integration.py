"""
Интеграционный слой между Ecology-BI и eco_modules.
Соединяет бизнес-логику друга с вашим PySide6 интерфейсом.
"""

import pandas as pd
from typing import Dict, Any, Tuple, Optional
from eco_modules import (
    get_kpi,
    get_by_category,
    get_by_omsu,
    get_by_mro,
    get_time_series,
    get_trash_analysis,
    load_excel,
    export_excel,
)


class EcoDashboardIntegration:
    """
    Интеграция экологического дашборда в Ecology-BI.
    
    Использование:
        eco = EcoDashboardIntegration(main_window)
        eco.load_data("file.xlsx")
        kpi = eco.get_kpi_data()
    """
    
    def __init__(self, main_window=None):
        self.main_window = main_window
        self.data: Optional[pd.DataFrame] = None
        self.report: Optional[Dict] = None
        self._filters: Dict[str, Any] = {}
    
    def set_main_window(self, main_window):
        """Устанавливает главное окно"""
        self.main_window = main_window
    
    def load_data(self, file_path: str) -> Tuple[pd.DataFrame, Dict]:
        """
        Загружает данные через его data_loader.
        
        Returns:
            (df, report) — датафрейм и отчёт о загрузке
        """
        df, report = load_excel(file_path)
        self.data = df
        self.report = report
        return df, report
    
    def set_filters(self, filters: Dict[str, Any]):
        """Устанавливает фильтры для данных"""
        self._filters = filters
    
    def _apply_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Применяет фильтры к данным"""
        if df is None or len(df) == 0:
            return df
        
        filtered = df.copy()
        
        # Фильтр по датам
        if 'date_range' in self._filters:
            dr = self._filters['date_range']
            if dr and dr[0] and dr[1]:
                filtered = filtered[
                    filtered['date'].between(
                        pd.Timestamp(dr[0]), 
                        pd.Timestamp(dr[1]), 
                        inclusive='both'
                    )
                ]
        
        # Фильтр по категориям
        if 'categories' in self._filters and self._filters['categories']:
            filtered = filtered[
                filtered['category'].isin(self._filters['categories'])
            ]
        
        # Фильтр по МРО
        if 'mro' in self._filters and self._filters['mro']:
            filtered = filtered[
                filtered['mro'].isin(self._filters['mro'])
            ]
        
        # Фильтр по ОМСУ
        if 'omsu' in self._filters and self._filters['omsu']:
            filtered = filtered[
                filtered['omsu'].isin(self._filters['omsu'])
            ]
        
        # Фильтр по статусу
        if 'status' in self._filters and self._filters['status'] != 'все':
            filtered = filtered[
                filtered['status'] == self._filters['status']
            ]
        
        return filtered
    
    def get_filtered_data(self) -> pd.DataFrame:
        """Возвращает отфильтрованные данные"""
        if self.data is None:
            return pd.DataFrame()
        return self._apply_filters(self.data)
    
    def get_kpi_data(self) -> Dict:
        """Возвращает KPI для отображения"""
        df = self.get_filtered_data()
        if len(df) == 0:
            return {
                'total': 0,
                'done': 0,
                'in_progress': 0,
                'pct_done': '—',
                'omsu_count': 0,
                'category_count': 0,
                'period': '—',
            }
        return get_kpi(df)
    
    def get_category_data(self) -> pd.DataFrame:
        """Возвращает данные по категориям"""
        df = self.get_filtered_data()
        if len(df) == 0:
            return pd.DataFrame()
        return get_by_category(df)
    
    def get_omsu_data(self) -> pd.DataFrame:
        """Возвращает данные по ОМСУ"""
        df = self.get_filtered_data()
        if len(df) == 0:
            return pd.DataFrame()
        return get_by_omsu(df)
    
    def get_mro_data(self) -> pd.DataFrame:
        """Возвращает данные по МРО"""
        df = self.get_filtered_data()
        if len(df) == 0:
            return pd.DataFrame()
        return get_by_mro(df)
    
    def get_time_series(self, freq: str = 'D') -> pd.DataFrame:
        """Возвращает временной ряд"""
        df = self.get_filtered_data()
        if len(df) == 0:
            return pd.DataFrame()
        return get_time_series(df, freq)
    
    def get_trash_analysis(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Возвращает анализ по мусору"""
        df = self.get_filtered_data()
        if len(df) == 0:
            return pd.DataFrame(), pd.DataFrame()
        return get_trash_analysis(df)
    
    def export_report(self, filters_info: Dict = None) -> Optional[bytes]:
        """Экспортирует Excel-отчёт"""
        df = self.get_filtered_data()
        if len(df) == 0:
            return None
        
        if filters_info is None:
            filters_info = {
                'Период': str(self._filters.get('date_range', 'Все')),
                'Категории': ', '.join(self._filters.get('categories', [])),
                'МРО': ', '.join(self._filters.get('mro', [])),
                'ОМСУ': ', '.join(self._filters.get('omsu', [])),
                'Статус': self._filters.get('status', 'Все'),
            }
        
        return export_excel(df, filters_info)
    
    def get_validation_report(self) -> Dict:
        """Возвращает отчёт о валидации данных"""
        return self.report or {}
    
    def has_data(self) -> bool:
        """Проверяет, загружены ли данные"""
        return self.data is not None and len(self.data) > 0