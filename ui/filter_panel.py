from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QListWidget,
    QListWidgetItem, QGroupBox, QCheckBox,
    QLineEdit, QScrollArea
)
from PySide6.QtGui import QIcon
import pandas as pd


class FilterPanel(QWidget):
    """Панель глобальных фильтров для дашборда"""
    
    filter_changed = Signal(dict)  # Сигнал при изменении фильтра
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.datasets = {}
        self.current_dataset = None
        self.filters = {}
        self.filter_widgets = {}
        self.df = None
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Заголовок
        title = QLabel("🔍 Global Filters")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Область прокрутки для фильтров
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        self.filter_container = QWidget()
        self.filter_layout = QVBoxLayout(self.filter_container)
        self.filter_layout.setSpacing(8)
        
        scroll.setWidget(self.filter_container)
        layout.addWidget(scroll)
        
        # Кнопка сброса всех фильтров
        reset_btn = QPushButton("🔄 Reset All Filters")
        reset_btn.clicked.connect(self.reset_all_filters)
        layout.addWidget(reset_btn)
        
        # Информация о фильтрах
        self.info_label = QLabel("No filters active")
        self.info_label.setStyleSheet("color: #888; font-size: 11px; padding: 5px;")
        layout.addWidget(self.info_label)
    
    def set_dataset(self, df, dataset_name):
        """Устанавливает датасет для фильтрации"""
        self.current_dataset = dataset_name
        self.df = df
        
        # Очищаем старые фильтры
        self.clear_filters()
        
        # Создаём фильтры для каждой колонки (кроме числовых с большим количеством уникальных значений)
        for col in df.columns:
            # Пропускаем колонки с большим количеством уникальных значений
            if len(df[col].unique()) > 50:
                continue
            
            # Создаём виджет фильтра
            self._create_filter_widget(col, df[col].unique())
    
    def clear_filters(self):
        """Очищает все фильтры"""
        # Очищаем контейнер
        for i in reversed(range(self.filter_layout.count())):
            widget = self.filter_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        self.filter_widgets.clear()
        self.filters.clear()
        self.update_info()
    
    def _create_filter_widget(self, column, values):
        """Создаёт виджет фильтра для колонки"""
        group = QGroupBox(column)
        group_layout = QVBoxLayout(group)
        
        # Чекбокс включения фильтра
        enable_check = QCheckBox("Enable Filter")
        enable_check.stateChanged.connect(
            lambda state, col=column: self._on_filter_toggle(col, state)
        )
        group_layout.addWidget(enable_check)
        
        # Выбор значений
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.MultiSelection)
        list_widget.setMaximumHeight(100)
        
        # Добавляем уникальные значения (сортировка)
        sorted_values = sorted([str(v) for v in values if pd.notna(v)])
        for val in sorted_values[:30]:  # Ограничиваем количество
            item = QListWidgetItem(val)
            list_widget.addItem(item)
        
        list_widget.itemSelectionChanged.connect(
            lambda col=column: self._on_filter_selection(col)
        )
        group_layout.addWidget(list_widget)
        
        # Кнопка выбора всех
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(
            lambda: self._select_all(list_widget)
        )
        group_layout.addWidget(select_all_btn)
        
        # Кнопка очистки выбора
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(
            lambda: self._clear_selection(list_widget)
        )
        group_layout.addWidget(clear_btn)
        
        # Сохраняем виджеты
        self.filter_widgets[column] = {
            'group': group,
            'list': list_widget,
            'enable': enable_check
        }
        
        self.filter_layout.addWidget(group)
    
    def _on_filter_toggle(self, column, state):
        """Включение/отключение фильтра"""
        if state == Qt.Checked:
            # Активируем фильтр
            selected = self._get_selected_values(column)
            if selected:
                self.filters[column] = selected
            else:
                # Если ничего не выбрано, выбираем все
                self._select_all(self.filter_widgets[column]['list'])
                self.filters[column] = self._get_selected_values(column)
        else:
            # Отключаем фильтр
            if column in self.filters:
                del self.filters[column]
        
        self.update_info()
        self.filter_changed.emit(self.filters)
    
    def _on_filter_selection(self, column):
        """Обработка изменения выбора в фильтре"""
        if column not in self.filter_widgets:
            return
        
        # Проверяем, включен ли фильтр
        enable_check = self.filter_widgets[column]['enable']
        if not enable_check.isChecked():
            return
        
        selected = self._get_selected_values(column)
        
        if selected:
            self.filters[column] = selected
        else:
            # Если ничего не выбрано, удаляем фильтр
            if column in self.filters:
                del self.filters[column]
        
        self.update_info()
        self.filter_changed.emit(self.filters)
    
    def _get_selected_values(self, column):
        """Возвращает выбранные значения для колонки"""
        list_widget = self.filter_widgets[column]['list']
        selected = []
        for item in list_widget.selectedItems():
            selected.append(item.text())
        return selected
    
    def _select_all(self, list_widget):
        """Выбирает все элементы в списке"""
        for i in range(list_widget.count()):
            list_widget.item(i).setSelected(True)
    
    def _clear_selection(self, list_widget):
        """Очищает выбор в списке"""
        list_widget.clearSelection()
    
    def reset_all_filters(self):
        """Сбрасывает все фильтры"""
        for col, widgets in self.filter_widgets.items():
            # Отключаем чекбокс
            widgets['enable'].setChecked(False)
            # Очищаем выбор
            self._clear_selection(widgets['list'])
        
        self.filters.clear()
        self.update_info()
        self.filter_changed.emit(self.filters)
    
    def update_info(self):
        """Обновляет информацию о активных фильтрах"""
        if not self.filters:
            self.info_label.setText("No filters active")
            return
        
        filter_text = "Active filters: "
        filter_parts = []
        for col, values in self.filters.items():
            if len(values) > 3:
                filter_parts.append(f"{col}: {len(values)} values")
            else:
                filter_parts.append(f"{col}: {', '.join(values)}")
        
        self.info_label.setText(filter_text + " | ".join(filter_parts))
    
    def apply_filters(self, df):
        """Применяет фильтры к датафрейму"""
        if not self.filters:
            return df
        
        filtered_df = df.copy()
        for col, values in self.filters.items():
            if col in filtered_df.columns:
                # Преобразуем значения в строки для сравнения
                filtered_df = filtered_df[filtered_df[col].astype(str).isin([str(v) for v in values])]
        
        return filtered_df
    
    def get_active_filters(self):
        """Возвращает активные фильтры"""
        return self.filters
    
    def set_active_filters(self, filters: dict):
        """Устанавливает активные фильтры (для синхронизации с кликами)"""
        self.filters = filters.copy()
        
        # Обновляем UI
        for col, widgets in self.filter_widgets.items():
            if col in filters:
                widgets['enable'].setChecked(True)
                list_widget = widgets['list']
                list_widget.clearSelection()
                for i in range(list_widget.count()):
                    item = list_widget.item(i)
                    if item.text() in filters[col]:
                        item.setSelected(True)
            else:
                widgets['enable'].setChecked(False)
        
        self.update_info()