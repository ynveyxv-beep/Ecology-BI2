# widgets/factory/dashboard_widget_factory.py
from widgets.dashboard.base_widget import BaseDashboardWidget
from widgets.dashboard.kpi_widget import KPIWidget
from widgets.dashboard.chart_widget import ChartWidget
from widgets.dashboard.table_widget import TableWidget

# BUG 2 FIX: import stub widgets so gauge/progress/pivot types are registered
from widgets.dashboard.stub_widgets import GaugeWidget, ProgressWidget, PivotWidget

try:
    from widgets.dashboard.map_widget import MapWidget
except ImportError:
    MapWidget = None

try:
    from widgets.dashboard.text_widget import TextWidget
except ImportError:
    TextWidget = None

try:
    from widgets.dashboard.image_widget import ImageWidget
except ImportError:
    ImageWidget = None


class DashboardWidgetFactory:
    """Фабрика для создания виджетов дашборда."""

    _registry = {
        'kpi':      KPIWidget,
        'chart':    ChartWidget,
        'table':    TableWidget,
        # BUG 2 FIX: register stub widget types so they can be created
        'gauge':    GaugeWidget,
        'progress': ProgressWidget,
        'pivot':    PivotWidget,
    }

    # Регистрируем только доступные виджеты
    if MapWidget is not None:
        _registry['map'] = MapWidget
    if TextWidget is not None:
        _registry['text'] = TextWidget
    if ImageWidget is not None:
        _registry['image'] = ImageWidget

    @classmethod
    def create(cls, widget_type: str, settings: dict = None) -> BaseDashboardWidget:
        """
        Создаёт виджет заданного типа.

        Args:
            widget_type: Тип виджета ('kpi', 'chart', 'table', 'text', 'image',
                         'map', 'gauge', 'progress', 'pivot')
            settings: Настройки виджета

        Returns:
            Экземпляр BaseDashboardWidget

        Raises:
            ValueError: Если тип виджета не зарегистрирован
        """
        if widget_type not in cls._registry:
            raise ValueError(f"Неизвестный тип виджета: {widget_type}")
        return cls._registry[widget_type](settings)

    @classmethod
    def get_types(cls) -> list:
        """Возвращает список доступных типов виджетов."""
        return list(cls._registry.keys())

    @classmethod
    def register(cls, widget_type: str, widget_class):
        """Регистрирует новый тип виджета."""
        if not issubclass(widget_class, BaseDashboardWidget):
            raise ValueError(f"{widget_class} должен наследоваться от BaseDashboardWidget")
        cls._registry[widget_type] = widget_class
