# ui/chart_settings_dialog.py
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QGroupBox, QGridLayout, QCheckBox, QColorDialog,
    QTabWidget, QWidget, QSlider, QLineEdit, QRadioButton
)
from PySide6.QtGui import QColor, QFont


class ChartSettingsDialog(QDialog):
    """Диалог настроек графика"""
    
    settings_applied = Signal(dict)
    
    def __init__(self, current_settings: dict, parent=None):
        super().__init__(parent)
        self.current_settings = current_settings
        self.setWindowTitle("Настройки графика")
        self.setMinimumWidth(550)
        self.setMinimumHeight(450)
        
        self.init_ui()
        self.load_current_settings()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # ─── Вкладки настроек ──────────────────────────────────────────────
        tabs = QTabWidget()
        
        # Вкладка 1: Основные настройки
        tabs.addTab(self._create_general_tab(), "📊 Основные")
        
        # Вкладка 2: Агрегация и сортировка
        tabs.addTab(self._create_aggregation_tab(), "📈 Агрегация")
        
        # Вкладка 3: Внешний вид
        tabs.addTab(self._create_appearance_tab(), "🎨 Внешний вид")
        
        # Вкладка 4: Масштаб
        tabs.addTab(self._create_scale_tab(), "📏 Масштаб")
        
        layout.addWidget(tabs)
        
        # ─── Кнопки ─────────────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        
        reset_btn = QPushButton("🔄 Сбросить")
        reset_btn.clicked.connect(self.reset_settings)
        btn_layout.addWidget(reset_btn)
        
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("✅ Применить")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #1F4E79;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2a6b9e;
            }
        """)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_general_tab(self):
        """Создаёт вкладку основных настроек"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Тип графика
        group1 = QGroupBox("Тип графика")
        group1_layout = QGridLayout(group1)
        
        group1_layout.addWidget(QLabel("Тип:"), 0, 0)
        self.chart_type = QComboBox()
        self.chart_type.addItems(["Линия", "Столбцы", "Точки", "Область"])
        group1_layout.addWidget(self.chart_type, 0, 1)
        
        group1_layout.addWidget(QLabel("Толщина линии:"), 1, 0)
        self.line_width = QSpinBox()
        self.line_width.setRange(1, 10)
        self.line_width.setValue(2)
        group1_layout.addWidget(self.line_width, 1, 1)
        
        group1_layout.addWidget(QLabel("Размер точек:"), 2, 0)
        self.point_size = QSpinBox()
        self.point_size.setRange(1, 20)
        self.point_size.setValue(5)
        group1_layout.addWidget(self.point_size, 2, 1)
        
        layout.addWidget(group1)
        
        # Подписи
        group2 = QGroupBox("Подписи осей")
        group2_layout = QGridLayout(group2)
        
        group2_layout.addWidget(QLabel("Ось X:"), 0, 0)
        self.x_label = QLineEdit()
        self.x_label.setPlaceholderText("Название оси X")
        group2_layout.addWidget(self.x_label, 0, 1)
        
        group2_layout.addWidget(QLabel("Ось Y:"), 1, 0)
        self.y_label = QLineEdit()
        self.y_label.setPlaceholderText("Название оси Y")
        group2_layout.addWidget(self.y_label, 1, 1)
        
        group2_layout.addWidget(QLabel("Заголовок:"), 2, 0)
        self.title = QLineEdit()
        self.title.setPlaceholderText("Заголовок графика")
        group2_layout.addWidget(self.title, 2, 1)
        
        layout.addWidget(group2)
        
        # Легенда
        group3 = QGroupBox("Легенда")
        group3_layout = QHBoxLayout(group3)
        
        self.show_legend = QCheckBox("Показывать легенду")
        self.show_legend.setChecked(True)
        group3_layout.addWidget(self.show_legend)
        
        layout.addWidget(group3)
        
        layout.addStretch()
        
        return widget
    
    def _create_aggregation_tab(self):
        """Создаёт вкладку агрегации и сортировки"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # ─── Агрегация ──────────────────────────────────────────────────────
        group1 = QGroupBox("Агрегация данных")
        group1_layout = QGridLayout(group1)
        
        group1_layout.addWidget(QLabel("Группировка по:"), 0, 0)
        self.aggregation = QComboBox()
        self.aggregation.addItems(["Без агрегации", "По дням", "По неделям", "По месяцам", "По кварталам", "По годам"])
        self.aggregation.setToolTip("Группировка данных по временному периоду")
        group1_layout.addWidget(self.aggregation, 0, 1)
        
        group1_layout.addWidget(QLabel("Метод агрегации:"), 1, 0)
        self.agg_method = QComboBox()
        self.agg_method.addItems(["Сумма", "Среднее", "Максимум", "Минимум", "Количество"])
        self.agg_method.setToolTip("Как агрегировать данные в каждой группе")
        group1_layout.addWidget(self.agg_method, 1, 1)
        
        layout.addWidget(group1)
        
        # ─── Сортировка ─────────────────────────────────────────────────────
        group2 = QGroupBox("Сортировка")
        group2_layout = QGridLayout(group2)
        
        group2_layout.addWidget(QLabel("Сортировать по:"), 0, 0)
        self.sort_by = QComboBox()
        self.sort_by.addItems(["По дате", "По значению", "По категории"])
        group2_layout.addWidget(self.sort_by, 0, 1)
        
        group2_layout.addWidget(QLabel("Порядок:"), 1, 0)
        self.sort_order = QComboBox()
        self.sort_order.addItems(["По возрастанию", "По убыванию"])
        group2_layout.addWidget(self.sort_order, 1, 1)
        
        group2_layout.addWidget(QLabel("Лимит:"), 2, 0)
        self.limit = QSpinBox()
        self.limit.setRange(0, 100)
        self.limit.setValue(0)
        self.limit.setToolTip("0 - без ограничений")
        group2_layout.addWidget(self.limit, 2, 1)
        
        layout.addWidget(group2)
        
        # ─── Дополнительно ──────────────────────────────────────────────────
        group3 = QGroupBox("Дополнительно")
        group3_layout = QVBoxLayout(group3)
        
        self.reverse_order = QCheckBox("Инвертировать порядок (последние сверху)")
        group3_layout.addWidget(self.reverse_order)
        
        self.show_trend = QCheckBox("Показывать линию тренда")
        group3_layout.addWidget(self.show_trend)
        
        layout.addWidget(group3)
        
        layout.addStretch()
        
        return widget
    
    def _create_appearance_tab(self):
        """Создаёт вкладку внешнего вида"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Цвета
        group1 = QGroupBox("Цвета")
        group1_layout = QGridLayout(group1)
        
        group1_layout.addWidget(QLabel("Основной цвет:"), 0, 0)
        self.main_color_btn = QPushButton("Выбрать цвет")
        self.main_color_btn.clicked.connect(lambda: self._pick_color('main'))
        self.main_color_preview = QLabel("  ")
        self.main_color_preview.setStyleSheet("background-color: #1F4E79; border: 1px solid #000; min-width: 30px; min-height: 20px;")
        group1_layout.addWidget(self.main_color_preview, 0, 1)
        group1_layout.addWidget(self.main_color_btn, 0, 2)
        
        group1_layout.addWidget(QLabel("Цвет фона:"), 1, 0)
        self.bg_color_btn = QPushButton("Выбрать цвет")
        self.bg_color_btn.clicked.connect(lambda: self._pick_color('bg'))
        self.bg_color_preview = QLabel("  ")
        self.bg_color_preview.setStyleSheet("background-color: white; border: 1px solid #000; min-width: 30px; min-height: 20px;")
        group1_layout.addWidget(self.bg_color_preview, 1, 1)
        group1_layout.addWidget(self.bg_color_btn, 1, 2)
        
        layout.addWidget(group1)
        
        # Шрифты
        group2 = QGroupBox("Шрифты")
        group2_layout = QGridLayout(group2)
        
        group2_layout.addWidget(QLabel("Размер шрифта:"), 0, 0)
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 20)
        self.font_size.setValue(10)
        group2_layout.addWidget(self.font_size, 0, 1)
        
        layout.addWidget(group2)
        
        layout.addStretch()
        
        return widget
    
    def _create_scale_tab(self):
        """Создаёт вкладку настроек масштаба"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        group1 = QGroupBox("Масштаб")
        group1_layout = QGridLayout(group1)
        
        group1_layout.addWidget(QLabel("Режим:"), 0, 0)
        self.scale_mode = QComboBox()
        self.scale_mode.addItems(["Авто", "Ручной"])
        self.scale_mode.currentTextChanged.connect(self._on_scale_mode_changed)
        group1_layout.addWidget(self.scale_mode, 0, 1)
        
        # Ручной масштаб
        self.manual_scale_widget = QWidget()
        manual_layout = QGridLayout(self.manual_scale_widget)
        manual_layout.setContentsMargins(0, 10, 0, 0)
        
        manual_layout.addWidget(QLabel("Min X:"), 0, 0)
        self.min_x = QDoubleSpinBox()
        self.min_x.setRange(-10000, 10000)
        self.min_x.setValue(0)
        self.min_x.setEnabled(False)
        manual_layout.addWidget(self.min_x, 0, 1)
        
        manual_layout.addWidget(QLabel("Max X:"), 0, 2)
        self.max_x = QDoubleSpinBox()
        self.max_x.setRange(-10000, 10000)
        self.max_x.setValue(100)
        self.max_x.setEnabled(False)
        manual_layout.addWidget(self.max_x, 0, 3)
        
        manual_layout.addWidget(QLabel("Min Y:"), 1, 0)
        self.min_y = QDoubleSpinBox()
        self.min_y.setRange(-10000, 10000)
        self.min_y.setValue(0)
        self.min_y.setEnabled(False)
        manual_layout.addWidget(self.min_y, 1, 1)
        
        manual_layout.addWidget(QLabel("Max Y:"), 1, 2)
        self.max_y = QDoubleSpinBox()
        self.max_y.setRange(-10000, 10000)
        self.max_y.setValue(100)
        self.max_y.setEnabled(False)
        manual_layout.addWidget(self.max_y, 1, 3)
        
        group1_layout.addWidget(self.manual_scale_widget, 1, 0, 1, 2)
        
        layout.addWidget(group1)
        
        # Интерактивность
        group2 = QGroupBox("Интерактивность")
        group2_layout = QVBoxLayout(group2)
        
        self.enable_zoom = QCheckBox("Разрешить масштабирование колесиком мыши")
        self.enable_zoom.setChecked(False)
        group2_layout.addWidget(self.enable_zoom)
        
        self.enable_pan = QCheckBox("Разрешить перемещение")
        self.enable_pan.setChecked(False)
        group2_layout.addWidget(self.enable_pan)
        
        layout.addWidget(group2)
        
        layout.addStretch()
        
        return widget
    
    def _pick_color(self, target: str):
        """Открывает диалог выбора цвета"""
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name()
            if target == 'main':
                self.main_color_preview.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #000; min-width: 30px; min-height: 20px;")
                self._main_color = hex_color
            else:
                self.bg_color_preview.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #000; min-width: 30px; min-height: 20px;")
                self._bg_color = hex_color
    
    def _on_scale_mode_changed(self, mode: str):
        """Обрабатывает смену режима масштаба"""
        is_manual = mode == "Ручной"
        self.min_x.setEnabled(is_manual)
        self.max_x.setEnabled(is_manual)
        self.min_y.setEnabled(is_manual)
        self.max_y.setEnabled(is_manual)
    
    def load_current_settings(self):
        """Загружает текущие настройки"""
        settings = self.current_settings
        
        # Основные
        self.chart_type.setCurrentText(settings.get('chart_type', 'Линия'))
        self.line_width.setValue(settings.get('line_width', 2))
        self.point_size.setValue(settings.get('point_size', 5))
        
        # Подписи
        self.x_label.setText(settings.get('x_label', ''))
        self.y_label.setText(settings.get('y_label', ''))
        self.title.setText(settings.get('title', ''))
        
        # Легенда
        self.show_legend.setChecked(settings.get('show_legend', True))
        
        # Цвета
        main_color = settings.get('main_color', '#1F4E79')
        self.main_color_preview.setStyleSheet(f"background-color: {main_color}; border: 1px solid #000; min-width: 30px; min-height: 20px;")
        self._main_color = main_color
        
        bg_color = settings.get('bg_color', '#ffffff')
        self.bg_color_preview.setStyleSheet(f"background-color: {bg_color}; border: 1px solid #000; min-width: 30px; min-height: 20px;")
        self._bg_color = bg_color
        
        # Шрифт
        self.font_size.setValue(settings.get('font_size', 10))
        
        # Масштаб
        self.scale_mode.setCurrentText(settings.get('scale_mode', 'Авто'))
        self.min_x.setValue(settings.get('min_x', 0))
        self.max_x.setValue(settings.get('max_x', 100))
        self.min_y.setValue(settings.get('min_y', 0))
        self.max_y.setValue(settings.get('max_y', 100))
        self._on_scale_mode_changed(self.scale_mode.currentText())
        
        # Интерактивность (по умолчанию выключена)
        self.enable_zoom.setChecked(settings.get('enable_zoom', False))
        self.enable_pan.setChecked(settings.get('enable_pan', False))
        
        # ─── Агрегация ──────────────────────────────────────────────────────
        self.aggregation.setCurrentText(settings.get('aggregation', 'Без агрегации'))
        self.agg_method.setCurrentText(settings.get('agg_method', 'Сумма'))
        
        # ─── Сортировка ─────────────────────────────────────────────────────
        self.sort_by.setCurrentText(settings.get('sort_by', 'По дате'))
        self.sort_order.setCurrentText(settings.get('sort_order', 'По возрастанию'))
        self.limit.setValue(settings.get('limit', 0))
        self.reverse_order.setChecked(settings.get('reverse_order', False))
        self.show_trend.setChecked(settings.get('show_trend', False))
    
    def reset_settings(self):
        """Сбрасывает настройки к значениям по умолчанию"""
        # Основные
        self.chart_type.setCurrentText("Линия")
        self.line_width.setValue(2)
        self.point_size.setValue(5)
        self.x_label.clear()
        self.y_label.clear()
        self.title.clear()
        self.show_legend.setChecked(True)
        self.font_size.setValue(10)
        
        # Цвета
        self.main_color_preview.setStyleSheet("background-color: #1F4E79; border: 1px solid #000; min-width: 30px; min-height: 20px;")
        self._main_color = "#1F4E79"
        self.bg_color_preview.setStyleSheet("background-color: white; border: 1px solid #000; min-width: 30px; min-height: 20px;")
        self._bg_color = "#ffffff"
        
        # Масштаб
        self.scale_mode.setCurrentText("Авто")
        self.enable_zoom.setChecked(False)
        self.enable_pan.setChecked(False)
        self._on_scale_mode_changed("Авто")
        
        # Агрегация
        self.aggregation.setCurrentText("Без агрегации")
        self.agg_method.setCurrentText("Сумма")
        
        # Сортировка
        self.sort_by.setCurrentText("По дате")
        self.sort_order.setCurrentText("По возрастанию")
        self.limit.setValue(0)
        self.reverse_order.setChecked(False)
        self.show_trend.setChecked(False)
    
    def apply_settings(self):
        """Применяет настройки"""
        settings = {
            # Основные
            'chart_type': self.chart_type.currentText(),
            'line_width': self.line_width.value(),
            'point_size': self.point_size.value(),
            
            # Подписи
            'x_label': self.x_label.text(),
            'y_label': self.y_label.text(),
            'title': self.title.text(),
            
            # Легенда
            'show_legend': self.show_legend.isChecked(),
            
            # Цвета
            'main_color': getattr(self, '_main_color', '#1F4E79'),
            'bg_color': getattr(self, '_bg_color', '#ffffff'),
            
            # Шрифт
            'font_size': self.font_size.value(),
            
            # Масштаб
            'scale_mode': self.scale_mode.currentText(),
            'min_x': self.min_x.value(),
            'max_x': self.max_x.value(),
            'min_y': self.min_y.value(),
            'max_y': self.max_y.value(),
            
            # Интерактивность
            'enable_zoom': self.enable_zoom.isChecked(),
            'enable_pan': self.enable_pan.isChecked(),
            
            # ─── Агрегация ──────────────────────────────────────────────────
            'aggregation': self.aggregation.currentText(),
            'agg_method': self.agg_method.currentText(),
            
            # ─── Сортировка ──────────────────────────────────────────────────
            'sort_by': self.sort_by.currentText(),
            'sort_order': self.sort_order.currentText(),
            'limit': self.limit.value(),
            'reverse_order': self.reverse_order.isChecked(),
            'show_trend': self.show_trend.isChecked(),
        }
        
        self.settings_applied.emit(settings)
        self.accept()