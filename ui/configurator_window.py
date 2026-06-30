# ui/configurator_window.py
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QScrollArea,
    QTabWidget, QListWidget, QListWidgetItem,
    QSplitter, QFrame, QGridLayout, QComboBox,
    QLineEdit, QGroupBox, QCheckBox, QSpinBox
)
from PySide6.QtGui import QDragEnterEvent, QDropEvent

import os
import json
import pandas as pd
from datetime import datetime

from logger import logger, LoggerMixin


class ConfiguratorWindow(QWidget, LoggerMixin):
    """Конструктор дашбордов - позволяет создавать и настраивать дашборды"""
    
    back_clicked = Signal()
    dashboard_created = Signal(str)  # сигнал о создании дашборда
    
    def __init__(self):
        super().__init__()
        self.log.info("🚀 Инициализация ConfiguratorWindow")
        
        self.current_dashboard = None
        self.widgets_list = []
        self.data = None
        
        self.init_ui()
        self.load_templates()
        
        self.log.info("✅ ConfiguratorWindow инициализирован")
    
    def init_ui(self):
        """Инициализация интерфейса"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ─── Верхняя панель ─────────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setStyleSheet("background: #f8f9fa; padding: 5px; border-bottom: 1px solid #dee2e6;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        back_btn = QPushButton("← Назад")
        back_btn.clicked.connect(self.go_back)
        toolbar_layout.addWidget(back_btn)
        
        toolbar_layout.addWidget(QLabel("|"))
        
        self.load_btn = QPushButton("📂 Загрузить данные")
        self.load_btn.clicked.connect(self.load_data)
        toolbar_layout.addWidget(self.load_btn)
        
        self.save_btn = QPushButton("💾 Сохранить шаблон")
        self.save_btn.clicked.connect(self.save_template)
        self.save_btn.setEnabled(False)
        toolbar_layout.addWidget(self.save_btn)
        
        self.load_template_btn = QPushButton("📂 Загрузить шаблон")
        self.load_template_btn.clicked.connect(self.load_template_file)
        toolbar_layout.addWidget(self.load_template_btn)
        
        toolbar_layout.addStretch()
        
        self.info_label = QLabel("Конструктор дашбордов")
        self.info_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        toolbar_layout.addWidget(self.info_label)
        
        main_layout.addWidget(toolbar)
        
        # ─── Основная область (сплиттер) ──────────────────────────────────
        splitter = QSplitter(Qt.Horizontal)
        
        # Левая панель - список виджетов
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # Правая панель - холст дашборда
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([300, 900])
        
        main_layout.addWidget(splitter)
    
    def _create_left_panel(self):
        """Создаёт левую панель с виджетами"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Заголовок
        title = QLabel("📊 Компоненты дашборда")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Список доступных виджетов
        self.widget_list = QListWidget()
        self.widget_list.setStyleSheet("""
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #dee2e6;
            }
            QListWidget::item:hover {
                background-color: #e9ecef;
            }
        """)
        
        # Добавляем виджеты
        widgets = [
            ("KPI-карточки", "Показывает ключевые показатели"),
            ("Временной ряд", "График динамики обращений"),
            ("Топ категорий", "График распределения по категориям"),
            ("Таблица данных", "Таблица с данными"),
            ("География", "Аналитика по ОМСУ/МРО"),
            ("Мусор", "Аналитика по мусору, свалкам, стокам"),
        ]
        
        for name, desc in widgets:
            item = QListWidgetItem(f"📊 {name}")
            item.setToolTip(desc)
            item.setData(Qt.UserRole, name)
            self.widget_list.addItem(item)
        
        self.widget_list.itemDoubleClicked.connect(self.add_widget_to_dashboard)
        layout.addWidget(self.widget_list)
        
        # Кнопка добавления
        add_btn = QPushButton("➕ Добавить виджет")
        add_btn.clicked.connect(lambda: self.add_widget_to_dashboard(self.widget_list.currentItem()))
        layout.addWidget(add_btn)
        
        # Кнопка удаления
        remove_btn = QPushButton("❌ Удалить виджет")
        remove_btn.clicked.connect(self.remove_selected_widget)
        layout.addWidget(remove_btn)
        
        layout.addStretch()
        
        return panel
    
    def _create_right_panel(self):
        """Создаёт правую панель - холст дашборда"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Заголовок
        title = QLabel("🖼️ Холст дашборда")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Настройки дашборда
        settings_group = QGroupBox("Настройки дашборда")
        settings_layout = QGridLayout(settings_group)
        
        settings_layout.addWidget(QLabel("Название:"), 0, 0)
        self.dashboard_name = QLineEdit()
        self.dashboard_name.setPlaceholderText("Введите название дашборда")
        settings_layout.addWidget(self.dashboard_name, 0, 1)
        
        settings_layout.addWidget(QLabel("Описание:"), 1, 0)
        self.dashboard_desc = QLineEdit()
        self.dashboard_desc.setPlaceholderText("Описание дашборда")
        settings_layout.addWidget(self.dashboard_desc, 1, 1)
        
        settings_layout.addWidget(QLabel("Макет:"), 2, 0)
        self.layout_type = QComboBox()
        self.layout_type.addItems(["Стандартный", "Компактный", "Широкий"])
        settings_layout.addWidget(self.layout_type, 2, 1)
        
        layout.addWidget(settings_group)
        
        # Холст
        self.canvas = QWidget()
        self.canvas.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border: 2px dashed #dee2e6;
                border-radius: 5px;
                min-height: 400px;
            }
        """)
        self.canvas_layout = QGridLayout(self.canvas)
        self.canvas_layout.setSpacing(10)
        self.canvas_layout.setContentsMargins(15, 15, 15, 15)
        
        # Счётчик виджетов на холсте
        self.widget_counter = 0
        self.canvas_widgets = {}
        
        layout.addWidget(self.canvas)
        
        # Информация
        self.canvas_info = QLabel("💡 Дважды кликните по виджету в списке слева, чтобы добавить его на холст")
        self.canvas_info.setStyleSheet("color: #6c757d; font-size: 12px; padding: 5px;")
        layout.addWidget(self.canvas_info)
        
        return panel
    
    def add_widget_to_dashboard(self, item):
        """Добавляет виджет на холст"""
        if item is None:
            QMessageBox.information(self, "Информация", "Выберите виджет из списка")
            return
        
        widget_name = item.data(Qt.UserRole)
        self.log.info(f"➕ Добавление виджета: {widget_name}")
        
        # Создаём контейнер для виджета
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(5, 5, 5, 5)
        
        # Заголовок виджета
        header = QHBoxLayout()
        label = QLabel(f"📊 {widget_name}")
        label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header.addWidget(label)
        header.addStretch()
        
        # Кнопка удаления виджета
        del_btn = QPushButton("✕")
        del_btn.setFixedSize(20, 20)
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        del_btn.clicked.connect(lambda: self.remove_widget_from_canvas(container))
        header.addWidget(del_btn)
        
        container_layout.addLayout(header)
        
        # Место для содержимого виджета
        content = QLabel("Содержимое виджета будет здесь")
        content.setStyleSheet("color: #6c757d; padding: 20px; background: #f8f9fa; border-radius: 3px;")
        content.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(content)
        
        # Добавляем на холст
        row = self.widget_counter // 2
        col = self.widget_counter % 2
        self.canvas_layout.addWidget(container, row, col)
        
        self.canvas_widgets[self.widget_counter] = {
            'widget': container,
            'name': widget_name,
            'row': row,
            'col': col
        }
        self.widget_counter += 1
        
        self.save_btn.setEnabled(True)
        self.canvas_info.setText(f"✅ Добавлено {self.widget_counter} виджет(ов)")
        
        self.log.info(f"✅ Виджет добавлен: {widget_name} (row={row}, col={col})")
    
    def remove_widget_from_canvas(self, container):
        """Удаляет виджет с холста"""
        # Находим виджет по контейнеру
        for key, data in list(self.canvas_widgets.items()):
            if data['widget'] == container:
                container.deleteLater()
                del self.canvas_widgets[key]
                self.widget_counter -= 1
                self.canvas_info.setText(f"✅ Осталось {self.widget_counter} виджет(ов)")
                self.log.info(f"❌ Виджет удалён: {data['name']}")
                break
        
        if self.widget_counter == 0:
            self.save_btn.setEnabled(False)
    
    def remove_selected_widget(self):
        """Удаляет выбранный виджет (если реализовать выбор)"""
        # Для простоты удаляем последний добавленный
        if self.widget_counter > 0:
            last_key = max(self.canvas_widgets.keys())
            data = self.canvas_widgets[last_key]
            self.remove_widget_from_canvas(data['widget'])
        else:
            QMessageBox.information(self, "Информация", "Нет виджетов для удаления")
    
    def load_data(self):
        """Загружает данные для дашборда"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Загрузить данные", "", "Excel (*.xlsx *.xls);;CSV (*.csv)"
        )
        
        if not path:
            return
        
        try:
            self.log.info(f"📂 Загрузка данных: {path}")
            
            if path.endswith('.csv'):
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path, engine='openpyxl')
            
            if df is None or len(df) == 0:
                QMessageBox.warning(self, "Предупреждение", "Файл пуст")
                return
            
            self.data = df
            self.info_label.setText(f"✅ Данные загружены: {len(df)} строк")
            QMessageBox.information(self, "Успех", f"Загружено {len(df)} строк")
            
        except Exception as e:
            self.log.error(f"❌ Ошибка загрузки: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def save_template(self):
        """Сохраняет шаблон дашборда"""
        if self.widget_counter == 0:
            QMessageBox.warning(self, "Предупреждение", "Добавьте хотя бы один виджет")
            return
        
        name = self.dashboard_name.text().strip()
        if not name:
            name = f"Дашборд_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Собираем информацию о дашборде
        template = {
            'name': name,
            'description': self.dashboard_desc.text(),
            'layout': self.layout_type.currentText(),
            'created_at': datetime.now().isoformat(),
            'widgets': []
        }
        
        for key, data in self.canvas_widgets.items():
            template['widgets'].append({
                'id': key,
                'type': data['name'],
                'row': data['row'],
                'col': data['col']
            })
        
        # Сохраняем в файл
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить шаблон", f"{name}.json", "JSON (*.json)"
        )
        
        if not path:
            return
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
            
            self.log.info(f"✅ Шаблон сохранён: {path}")
            QMessageBox.information(self, "Успех", f"Шаблон сохранён:\n{path}")
            
        except Exception as e:
            self.log.error(f"❌ Ошибка сохранения: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def load_template_file(self):
        """Загружает шаблон из файла"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Загрузить шаблон", "", "JSON (*.json)"
        )
        
        if not path:
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                template = json.load(f)
            
            self.log.info(f"📂 Загружен шаблон: {path}")
            self.log.debug(f"Шаблон: {template}")
            
            # Очищаем текущий холст
            for key in list(self.canvas_widgets.keys()):
                data = self.canvas_widgets[key]
                data['widget'].deleteLater()
                del self.canvas_widgets[key]
            
            self.widget_counter = 0
            
            # Заполняем информацию о дашборде
            self.dashboard_name.setText(template.get('name', ''))
            self.dashboard_desc.setText(template.get('description', ''))
            
            idx = self.layout_type.findText(template.get('layout', 'Стандартный'))
            if idx >= 0:
                self.layout_type.setCurrentIndex(idx)
            
            # Добавляем виджеты
            for widget_data in template.get('widgets', []):
                # Создаём виртуальный элемент списка
                item = QListWidgetItem()
                item.setData(Qt.UserRole, widget_data['type'])
                self.add_widget_to_dashboard(item)
            
            self.save_btn.setEnabled(self.widget_counter > 0)
            self.log.info(f"✅ Шаблон загружен: {template.get('name')}")
            QMessageBox.information(self, "Успех", f"Шаблон загружен:\n{template.get('name')}")
            
        except Exception as e:
            self.log.error(f"❌ Ошибка загрузки шаблона: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def load_templates(self):
        """Загружает предустановленные шаблоны"""
        # Здесь можно добавить загрузку шаблонов из папки templates/
        pass
    
    def go_back(self):
        self.log.info("⬅️ Возврат")
        self.back_clicked.emit()