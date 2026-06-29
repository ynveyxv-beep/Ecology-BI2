"""
eco_modules — бизнес-логика экологического дашборда.
Взято из eco-dashboard (al0neintokyo/eco-dashboard).
Имена файлов переименованы для избежания конфликтов.
"""

from .eco_metrics import (
    get_kpi,
    get_by_category,
    get_by_omsu,
    get_by_mro,
    get_time_series,
    get_trash_analysis,
)
from .eco_data_loader import load_excel, OMSU_SYNONYMS, load_excel_with_report
from .eco_report_excel import export_excel

__all__ = [
    'get_kpi',
    'get_by_category',
    'get_by_omsu',
    'get_by_mro',
    'get_time_series',
    'get_trash_analysis',
    'load_excel',
    'load_excel_with_report',
    'OMSU_SYNONYMS',
    'export_excel',
]