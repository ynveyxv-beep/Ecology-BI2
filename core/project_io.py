import json
import pandas as pd
from typing import List, Dict, Any


class ProjectIO:
    """Сохранение и загрузка проектов"""
    
    @staticmethod
    def save(path: str, items: List, df: pd.DataFrame = None, filters: Dict = None):
        """Сохраняет проект в JSON"""
        
        data = {
            "version": "1.0",
            "filters": filters or {},
            "dataset": None,
            "items": []
        }
        
        if df is not None:
            data["dataset"] = df.replace([float('inf'), float('-inf')], None).fillna('').to_json(orient='split')
        
        for item in items:
            item_data = {
                "type": "plot",
                "chart_type": getattr(item, "chart_type", "scatter"),
                "x": float(item.x()),
                "y": float(item.y()),
                "width": int(item.chart_width),
                "height": int(item.chart_height),
                "x_column": getattr(item, "x_column", None),
                "y_column": getattr(item, "y_column", None),
            }
            data["items"].append(item_data)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    
    @staticmethod
    def load(path: str):
        """Загружает проект из JSON"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            df = None
            if data.get("dataset"):
                df = pd.read_json(data["dataset"], orient="split")

            return data, df
        except Exception as e:
            raise RuntimeError(f"Не удалось загрузить проект из {path}: {e}") from e