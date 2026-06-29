from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import uuid


@dataclass
class ChartConfig:
    """Конфигурация одного графика"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    chart_type: str = "line"
    
    # Данные
    dataset_name: str = ""
    x_column: str = ""
    y_columns: List[str] = field(default_factory=list)
    aggregation: str = "none"
    
    # Внешний вид
    title: str = ""
    color: str = "#0078d4"
    show_legend: bool = True
    width: int = 600
    height: int = 350
    
    # Позиция
    x: int = 0
    y: int = 0
    
    # Страница
    page: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "chart_type": self.chart_type,
            "dataset_name": self.dataset_name,
            "x_column": self.x_column,
            "y_columns": self.y_columns,
            "aggregation": self.aggregation,
            "title": self.title,
            "color": self.color,
            "show_legend": self.show_legend,
            "width": self.width,
            "height": self.height,
            "x": self.x,
            "y": self.y,
            "page": self.page
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChartConfig':
        return cls(**data)


@dataclass
class Page:
    """Модель одной страницы внутри дашборда"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Page 1"
    charts: List[ChartConfig] = field(default_factory=list)
    
    def add_chart(self, chart_config: ChartConfig) -> None:
        self.charts.append(chart_config)
    
    def remove_chart(self, chart_id: str) -> None:
        self.charts = [c for c in self.charts if c.id != chart_id]
    
    def get_chart(self, chart_id: str) -> Optional[ChartConfig]:
        for chart in self.charts:
            if chart.id == chart_id:
                return chart
        return None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "charts": [c.to_dict() for c in self.charts]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Page':
        page = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Page 1")
        )
        for chart_data in data.get("charts", []):
            page.add_chart(ChartConfig.from_dict(chart_data))
        return page


@dataclass
class Dashboard:
    """Модель одного дашборда (с несколькими страницами)"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Dashboard"
    pages: List[Page] = field(default_factory=list)
    current_page: int = 0
    
    def __post_init__(self):
        if not self.pages:
            self.pages.append(Page(name="Page 1"))
    
    def add_page(self, name: str = "New Page") -> Page:
        page = Page(name=name)
        self.pages.append(page)
        return page
    
    def remove_page(self, index: int) -> None:
        if len(self.pages) <= 1:
            return
        del self.pages[index]
        if self.current_page >= len(self.pages):
            self.current_page = len(self.pages) - 1
    
    def get_current_page(self) -> Page:
        if not self.pages:
            self.pages.append(Page(name="Page 1"))
        return self.pages[self.current_page]
    
    def switch_to_page(self, index: int) -> None:
        if 0 <= index < len(self.pages):
            self.current_page = index
    
    def get_page_names(self) -> List[str]:
        return [p.name for p in self.pages]
    
    def get_all_charts(self) -> List[ChartConfig]:
        all_charts = []
        for page in self.pages:
            all_charts.extend(page.charts)
        return all_charts
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "pages": [p.to_dict() for p in self.pages],
            "current_page": self.current_page
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Dashboard':
        dashboard = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "New Dashboard")
        )
        dashboard.pages = []
        for page_data in data.get("pages", []):
            dashboard.pages.append(Page.from_dict(page_data))
        dashboard.current_page = data.get("current_page", 0)
        return dashboard


class DashboardManager:
    """Управление всеми дашбордами"""
    
    def __init__(self):
        self.dashboards: List[Dashboard] = []
        self.current_index: int = 0
        self.add_dashboard("Dashboard 1")
    
    def add_dashboard(self, name: str = "New Dashboard") -> Dashboard:
        dashboard = Dashboard(name=name)
        self.dashboards.append(dashboard)
        return dashboard
    
    def remove_dashboard(self, index: int) -> None:
        if len(self.dashboards) > 1:
            del self.dashboards[index]
            if self.current_index >= len(self.dashboards):
                self.current_index = len(self.dashboards) - 1
    
    def get_current_dashboard(self) -> Dashboard:
        if not self.dashboards:
            self.add_dashboard()
        return self.dashboards[self.current_index]
    
    def switch_to_dashboard(self, index: int) -> None:
        if 0 <= index < len(self.dashboards):
            self.current_index = index
    
    def get_dashboard_names(self) -> List[str]:
        return [d.name for d in self.dashboards]
    
    def to_dict(self) -> Dict:
        return {
            "current_index": self.current_index,
            "dashboards": [d.to_dict() for d in self.dashboards]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DashboardManager':
        manager = cls()
        manager.dashboards = []
        for dash_data in data.get("dashboards", []):
            manager.dashboards.append(Dashboard.from_dict(dash_data))
        manager.current_index = data.get("current_index", 0)
        return manager


# Для обратной совместимости с экспортом
class DashboardPage:
    def __init__(self, name: str):
        self.name = name
        self.items = []