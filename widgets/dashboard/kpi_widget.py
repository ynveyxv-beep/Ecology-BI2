# widgets/dashboard/kpi_widget.py
import math
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QLabel

from widgets.dashboard.base_widget import BaseDashboardWidget

# Какие метрики доступны из eco_metrics.get_kpi()
KPI_METRICS = {
    'manual':        'Ручной ввод',
    'total':         'Всего обращений',
    'done':          'Выполнено',
    'in_progress':   'В работе',
    'pct_done':      '% выполнения',
    'omsu_count':    'Кол-во ОМСУ',
    'period':        'Период данных',
}


class KPIWidget(BaseDashboardWidget):
    """
    KPI-карточка.

    Настройки:
        metric      (str)  — ключ из KPI_METRICS; 'manual' = ручной ввод
        title       (str)  — подпись под значением
        value       (str)  — значение при metric='manual' (поддерживает любые строки)
        unit        (str)  — единица измерения (мкг/м³, шт. и т.д.)
        color       (str)  — цвет значения, HEX
        font_size   (int)  — размер шрифта значения
    """

    def __init__(self, settings: dict = None, parent=None):
        # Создаём лейблы ДО вызова super().__init__, т.к. тот вызывает set_settings → _apply_settings
        self._value_label = QLabel()
        self._value_label.setAlignment(Qt.AlignCenter)

        self._unit_label = QLabel()
        self._unit_label.setAlignment(Qt.AlignCenter)
        self._unit_label.hide()

        self._no_data_label = QLabel("Нет данных")
        self._no_data_label.setAlignment(Qt.AlignCenter)
        self._no_data_label.setStyleSheet("color: #64748B; font-size: 11px;")
        self._no_data_label.hide()

        super().__init__(settings, parent)

        self._content_layout.setAlignment(Qt.AlignCenter)
        self._content_layout.addWidget(self._value_label)
        self._content_layout.addWidget(self._unit_label)
        self._content_layout.addWidget(self._no_data_label)

    def _apply_settings(self):
        metric    = self._settings.get('metric', 'manual')
        color     = self._settings.get('color', '#38BDF8')
        font_size = self._settings.get('font_size', 36)
        # BUG 1 FIX: always read 'unit' from settings so it appears on the card
        unit      = self._settings.get('unit', '')

        value = self._resolve_value(metric)

        if value is None:
            # Данные ещё не загружены — показываем прочерк
            value = '—'

        self._no_data_label.hide()
        self._value_label.show()
        # BUG 1 FIX: display value as-is (supports plain text strings, not just numbers)
        self._value_label.setText(str(value))
        self._value_label.setStyleSheet(
            f"font-size: {font_size}px; font-weight: bold; color: {color};"
        )

        # BUG 1 FIX: always show unit label when unit is non-empty
        if unit:
            self._unit_label.setText(unit)
            self._unit_label.setStyleSheet(
                f"font-size: {max(11, font_size // 3)}px; color: {color}99;"
                f" margin-top: -4px;"
            )
            self._unit_label.show()
        else:
            self._unit_label.hide()

    def _resolve_value(self, metric: str):
        """Возвращает значение для отображения или None если данных нет."""
        if metric == 'manual' or not metric:
            # BUG 1 FIX: return raw value string without forcing numeric conversion —
            # this allows text format (arbitrary strings) to be displayed correctly.
            return self._settings.get('value', '—')

        if metric == 'column':
            col_name = self._settings.get('column_name', '')
            agg      = self._settings.get('aggregation', 'sum')
            if self._df is not None and col_name:
                if col_name not in self._df.columns:
                    return '—'
                try:
                    col = self._df[col_name].dropna()
                    if   agg == 'value':  val = col.iloc[0] if len(col) > 0 else '—'
                    elif agg == 'sum':    val = col.sum()
                    elif agg == 'avg':    val = round(float(col.mean()), 2)
                    elif agg == 'median': val = round(float(col.median()), 2)
                    elif agg == 'count':  val = len(col)
                    elif agg == 'unique': val = col.nunique()
                    elif agg == 'max':    val = col.max()
                    elif agg == 'min':    val = col.min()
                    elif agg == 'first':  val = col.iloc[0] if len(col) > 0 else '—'
                    elif agg == 'last':   val = col.iloc[-1] if len(col) > 0 else '—'
                    else:                 val = col.sum()
                    # Убираем .0 у целых чисел
                    if isinstance(val, float) and math.isfinite(val) and val == int(val):
                        val = int(val)
                    return str(val)
                except Exception as e:
                    print(f"KPIWidget: ошибка вычисления '{agg}' для '{col_name}': {e}")
                    return '—'
            return None  # Данные ещё не загружены

        # Eco-метрики (устаревший режим)
        if self._df is not None:
            try:
                from eco_modules.eco_metrics import get_kpi
                kpi = get_kpi(self._df)
                return kpi.get(metric, '—')
            except Exception as e:
                print(f"KPIWidget: ошибка получения метрики '{metric}': {e}")
                return '—'

        # Данные ещё не загружены — показываем плейсхолдер
        return None

    def settings(self) -> dict:
        # BUG 1 FIX: return a full copy including 'unit' so the edit dialog
        # pre-fills correctly and never shows wrong/missing values.
        return self._settings.copy()
