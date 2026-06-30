# ui/start_screen.py
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGridLayout, QFrame, QScrollArea,
    QListWidget, QListWidgetItem, QMessageBox
)
from PySide6.QtGui import QFont
import os
import json


class StartScreen(QWidget):
    """Стартовый экран с выбором шаблонов"""
    
    mode_selected = Signal(str)  # 'eco' или 'configurator'
    template_selected = Signal(str, str)  # 'load_template', path
    
    def __init__(self):
        super().__init__()
        self.templates_dir = "templates"
        os.makedirs(self.templates_dir, exist_ok=True)
        self.init_ui()
        self.load_saved_templates()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 30, 40, 30)
        
        # ─── Заголовок ──────────────────────────────────────────────────────
        title = QLabel("Ecology-BI")
        title.setStyleSheet("font-size: 36px; font-weight: bold; color: #1F4E79;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Система для экологического мониторинга и построения дашбордов")
        subtitle.setStyleSheet("font-size: 14px; color: #6c757d;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # ─── Два квадрата ──────────────────────────────────────────────────
        main_grid = QHBoxLayout()
        main_grid.setSpacing(20)
        
        # Левый квадрат - Экологический мониторинг
        left_card = self._create_eco_card()
        main_grid.addWidget(left_card, 1)
        
        # Правый квадрат - разделён на 3 секции
        right_card = self._create_tools_card()
        main_grid.addWidget(right_card, 1)
        
        layout.addLayout(main_grid)
        
        layout.addStretch()
    
    def _create_eco_card(self):
        """Создаёт карточку "Экологический мониторинг" (левый квадрат)"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box | QFrame.Raised)
        card.setStyleSheet("""
            QFrame {
                background-color: #f0f4f8;
                border: 2px solid #1F4E79;
                border-radius: 12px;
                padding: 20px;
            }
            QFrame:hover {
                background-color: #e8edf2;
                border-color: #2a6b9e;
            }
        """)
        card.setMinimumHeight(350)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(15)
        
        # Иконка
        icon = QLabel("🌿")
        icon.setStyleSheet("font-size: 48px;")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        
        # Заголовок
        title = QLabel("Экологический мониторинг")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F4E79;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Описание
        desc = QLabel(
            "Готовый дашборд с KPI, временным рядом,\n"
            "категориями, географией и аналитикой мусора"
        )
        desc.setStyleSheet("font-size: 13px; color: #6c757d;")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        layout.addStretch()
        
        # Кнопка
        btn = QPushButton("🚀 Открыть")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #1F4E79;
                color: white;
                padding: 12px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2a6b9e;
            }
        """)
        btn.clicked.connect(lambda: self.mode_selected.emit('eco'))
        layout.addWidget(btn)
        
        return card
    
    def _create_tools_card(self):
        """Создаёт карточку с инструментами (правый квадрат)"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box | QFrame.Raised)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #dee2e6;
                border-radius: 12px;
                padding: 15px;
            }
        """)
        card.setMinimumHeight(350)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        
        # Заголовок
        title = QLabel("🛠️ Конструктор дашбордов")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1F4E79;")
        layout.addWidget(title)
        
        # ─── 1. Конфигуратор ──────────────────────────────────────────────
        section1 = self._create_section(
            "🛠️ Конфигуратор",
            "Создайте новый дашборд с нуля",
            self._open_configurator
        )
        layout.addWidget(section1)
        
        # ─── 2. Последний сохранённый ────────────────────────────────────
        self.last_template_label = QLabel("💾 Последний сохранённый")
        self.last_template_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        
        self.last_template_name = QLabel("—")
        self.last_template_name.setStyleSheet("color: #6c757d; font-size: 12px;")
        
        last_btn = QPushButton("📂 Открыть последний")
        last_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        last_btn.clicked.connect(self._open_last_template)
        
        section2 = QWidget()
        section2_layout = QHBoxLayout(section2)
        section2_layout.setContentsMargins(0, 0, 0, 0)
        section2_layout.addWidget(self.last_template_label)
        section2_layout.addWidget(self.last_template_name)
        section2_layout.addStretch()
        section2_layout.addWidget(last_btn)
        section2.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 6px;
                padding: 8px 12px;
            }
        """)
        layout.addWidget(section2)
        
        # ─── 3. Выбор из сохранённых ──────────────────────────────────────
        section3_label = QLabel("📂 Выбор из сохранённых")
        section3_label.setStyleSheet("font-weight: bold; font-size: 13px; margin-top: 5px;")
        layout.addWidget(section3_label)
        
        self.templates_list = QListWidget()
        self.templates_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 5px;
                max-height: 100px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:hover {
                background-color: #e9ecef;
            }
        """)
        self.templates_list.itemDoubleClicked.connect(self._load_selected_template)
        layout.addWidget(self.templates_list)
        
        # Кнопка обновления списка
        refresh_btn = QPushButton("🔄 Обновить список")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 4px 8px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        refresh_btn.clicked.connect(self.load_saved_templates)
        
        refresh_layout = QHBoxLayout()
        refresh_layout.addStretch()
        refresh_layout.addWidget(refresh_btn)
        layout.addLayout(refresh_layout)
        
        # Загружаем последний сохранённый
        self._load_last_template_info()
        
        return card
    
    def _create_section(self, title: str, desc: str, callback):
        """Создаёт секцию в правом квадрате"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 6px;
                padding: 8px 12px;
            }
            QWidget:hover {
                background-color: #e9ecef;
            }
        """)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Текст
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        text_layout.addWidget(title_label)
        
        desc_label = QLabel(desc)
        desc_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout, 1)
        
        # Кнопка
        btn = QPushButton("Открыть")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #1F4E79;
                color: white;
                padding: 4px 12px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2a6b9e;
            }
        """)
        btn.clicked.connect(callback)
        layout.addWidget(btn)
        
        return widget
    
    def _open_configurator(self):
        """Открывает конфигуратор"""
        self.mode_selected.emit('configurator')
    
    def _open_last_template(self):
        """Открывает последний сохранённый шаблон"""
        last_path = self._get_last_template_path()
        if last_path and os.path.exists(last_path):
            self.template_selected.emit('load_template', last_path)
        else:
            QMessageBox.information(
                self, 
                "Информация", 
                "Нет сохранённых шаблонов.\n"
                "Сначала создайте дашборд в Конфигураторе и сохраните его."
            )
    
    def _load_selected_template(self, item):
        """Загружает выбранный шаблон"""
        if item:
            path = item.data(Qt.UserRole)
            if path and os.path.exists(path):
                self.template_selected.emit('load_template', path)
    
    def _get_last_template_path(self):
        """Возвращает путь к последнему сохранённому шаблону"""
        last_file = os.path.join(self.templates_dir, ".last_template")
        if os.path.exists(last_file):
            with open(last_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return None
    
    def _save_last_template_path(self, path):
        """Сохраняет путь к последнему шаблону"""
        last_file = os.path.join(self.templates_dir, ".last_template")
        with open(last_file, 'w', encoding='utf-8') as f:
            f.write(path)
        self._load_last_template_info()
    
    def _load_last_template_info(self):
        """Загружает информацию о последнем шаблоне"""
        last_path = self._get_last_template_path()
        if last_path and os.path.exists(last_path):
            try:
                with open(last_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    name = data.get('name', os.path.basename(last_path))
                    self.last_template_name.setText(name)
                    self.last_template_name.setStyleSheet("color: #28a745; font-size: 12px;")
            except:
                self.last_template_name.setText(os.path.basename(last_path))
                self.last_template_name.setStyleSheet("color: #6c757d; font-size: 12px;")
        else:
            self.last_template_name.setText("—")
            self.last_template_name.setStyleSheet("color: #6c757d; font-size: 12px;")
    
    def load_saved_templates(self):
        """Загружает список сохранённых шаблонов"""
        self.templates_list.clear()
        
        if not os.path.exists(self.templates_dir):
            return
        
        for file in os.listdir(self.templates_dir):
            if file.endswith('.json') and not file.startswith('.'):
                path = os.path.join(self.templates_dir, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        name = data.get('name', file)
                        desc = data.get('description', '')
                    
                    item = QListWidgetItem(f"📊 {name}")
                    item.setToolTip(desc or file)
                    item.setData(Qt.UserRole, path)
                    self.templates_list.addItem(item)
                except Exception as e:
                    self.log.warning(f"⚠️ Не удалось загрузить {file}: {e}")
                    item = QListWidgetItem(f"📄 {file}")
                    item.setData(Qt.UserRole, path)
                    self.templates_list.addItem(item)
    
    def update_last_template(self, path):
        """Обновляет информацию о последнем сохранённом шаблоне"""
        self._save_last_template_path(path)