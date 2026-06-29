from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QLineEdit, QListWidget,
    QListWidgetItem, QColorDialog, QGroupBox,
    QCheckBox, QSpinBox, QDoubleSpinBox
)
from PySide6.QtGui import QColor, QPalette


class PropertiesPanel(QWidget):
    """Панель свойств для настройки графиков"""
    
    property_changed = Signal(dict)
    apply_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_item = None
        self._is_updating = False
        self._main_window = None
        self.datasets = {}
        
        self.init_ui()
    
    def set_main_window(self, main_window):
        self._main_window = main_window
    
    def set_datasets(self, datasets: dict):
        """Устанавливает список доступных датасетов"""
        self._is_updating = True
        self.datasets = datasets
        self.dataset_combo.clear()
        self.dataset_combo.addItem("No dataset")
        for name in datasets.keys():
            self.dataset_combo.addItem(name)
        self._is_updating = False
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Заголовок
        title = QLabel("Chart Properties")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # --- ГРУППА: Данные ---
        data_group = QGroupBox("Data")
        data_layout = QVBoxLayout(data_group)
        
        # Выбор датасета
        dataset_label = QLabel("Dataset:")
        dataset_label.setStyleSheet("font-weight: bold;")
        data_layout.addWidget(dataset_label)
        
        self.dataset_combo = QComboBox()
        self.dataset_combo.addItem("No dataset")
        self.dataset_combo.currentTextChanged.connect(self._on_property_changed)
        data_layout.addWidget(self.dataset_combo)
        
        # Y-колонки
        y_label = QLabel("Y Columns:")
        y_label.setStyleSheet("font-weight: bold;")
        data_layout.addWidget(y_label)
        
        self.y_list = QListWidget()
        self.y_list.setSelectionMode(QListWidget.MultiSelection)
        self.y_list.itemSelectionChanged.connect(self._on_property_changed)
        data_layout.addWidget(self.y_list)
        
        # Агрегация
        agg_label = QLabel("Aggregation:")
        agg_label.setStyleSheet("font-weight: bold;")
        data_layout.addWidget(agg_label)
        
        self.agg_combo = QComboBox()
        self.agg_combo.addItems(["none", "SUM", "AVG", "COUNT", "MIN", "MAX", "MEDIAN"])
        self.agg_combo.currentTextChanged.connect(self._on_property_changed)
        data_layout.addWidget(self.agg_combo)
        
        layout.addWidget(data_group)
        
        # --- ГРУППА: Внешний вид ---
        style_group = QGroupBox("Style")
        style_layout = QVBoxLayout(style_group)
        
        title_label = QLabel("Title:")
        title_label.setStyleSheet("font-weight: bold;")
        style_layout.addWidget(title_label)
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Chart title...")
        self.title_edit.textChanged.connect(self._on_property_changed)
        style_layout.addWidget(self.title_edit)
        
        color_label = QLabel("Color:")
        color_label.setStyleSheet("font-weight: bold;")
        style_layout.addWidget(color_label)
        
        color_layout = QHBoxLayout()
        
        self.color_preview = QWidget()
        self.color_preview.setFixedSize(30, 30)
        self.color_preview.setStyleSheet("background-color: #0078d4; border: 1px solid #ccc; border-radius: 4px;")
        color_layout.addWidget(self.color_preview)
        
        self.color_btn = QPushButton("Choose Color")
        self.color_btn.clicked.connect(self._choose_color)
        color_layout.addWidget(self.color_btn)
        
        style_layout.addLayout(color_layout)
        
        self.legend_check = QCheckBox("Show Legend")
        self.legend_check.setChecked(True)
        self.legend_check.stateChanged.connect(self._on_property_changed)
        style_layout.addWidget(self.legend_check)
        
        layout.addWidget(style_group)
        
        # --- ГРУППА: Размер ---
        size_group = QGroupBox("Size")
        size_layout = QVBoxLayout(size_group)
        
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Width:"))
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(200, 2000)
        self.width_spin.setValue(600)
        self.width_spin.valueChanged.connect(self._on_property_changed)
        size_row.addWidget(self.width_spin)
        
        size_row.addWidget(QLabel("Height:"))
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(150, 1500)
        self.height_spin.setValue(350)
        self.height_spin.valueChanged.connect(self._on_property_changed)
        size_row.addWidget(self.height_spin)
        
        size_layout.addLayout(size_row)
        layout.addWidget(size_group)
        
        layout.addStretch()
        
        # Кнопки действий
        actions_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        self.apply_btn.clicked.connect(self.apply_changes)
        actions_layout.addWidget(self.apply_btn)
        
        layout.addLayout(actions_layout)
    
    def set_columns(self, columns: list):
        self._is_updating = True
        self.y_list.clear()
        for col in columns:
            item = QListWidgetItem(col)
            self.y_list.addItem(item)
        self._is_updating = False
    
    def set_properties(self, properties: dict):
        self._is_updating = True
        
        # Датасет
        dataset = properties.get("dataset_name", "")
        if dataset:
            index = self.dataset_combo.findText(dataset)
            if index >= 0:
                self.dataset_combo.setCurrentIndex(index)
        else:
            self.dataset_combo.setCurrentIndex(0)
        
        # Y-колонки
        y_cols = properties.get("y_columns", [])
        for i in range(self.y_list.count()):
            item = self.y_list.item(i)
            if item.text() in y_cols:
                item.setSelected(True)
            else:
                item.setSelected(False)
        
        # Агрегация
        agg = properties.get("aggregation", "none")
        index = self.agg_combo.findText(agg)
        if index >= 0:
            self.agg_combo.setCurrentIndex(index)
        
        # Заголовок
        self.title_edit.setText(properties.get("title", ""))
        
        # Цвет
        color = properties.get("color", "#0078d4")
        self.color_preview.setStyleSheet(f"background-color: {color}; border: 1px solid #ccc; border-radius: 4px;")
        
        # Легенда
        self.legend_check.setChecked(properties.get("show_legend", True))
        
        # Размер
        self.width_spin.setValue(properties.get("width", 600))
        self.height_spin.setValue(properties.get("height", 350))
        
        self._is_updating = False
    
    def get_properties(self) -> dict:
        return {
            "dataset_name": self.dataset_combo.currentText() if self.dataset_combo.currentIndex() > 0 else "",
            "y_columns": [item.text() for item in self.y_list.selectedItems()],
            "aggregation": self.agg_combo.currentText(),
            "title": self.title_edit.text(),
            "color": self.color_preview.styleSheet().split(":")[1].split(";")[0].strip(),
            "show_legend": self.legend_check.isChecked(),
            "width": self.width_spin.value(),
            "height": self.height_spin.value()
        }
    
    def _on_property_changed(self):
        if not self._is_updating:
            self.property_changed.emit(self.get_properties())
    
    def _choose_color(self):
        current_color = self.color_preview.styleSheet().split(":")[1].split(";")[0].strip()
        color = QColorDialog.getColor(QColor(current_color), self, "Choose Chart Color")
        if color.isValid():
            hex_color = color.name()
            self.color_preview.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #ccc; border-radius: 4px;")
            self._on_property_changed()
    
    def apply_changes(self):
        self.property_changed.emit(self.get_properties())
        self.apply_clicked.emit()
        if self._main_window and hasattr(self._main_window, 'statusBar'):
            self._main_window.statusBar().showMessage("✅ Properties applied", 2000)