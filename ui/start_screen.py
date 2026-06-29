from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QApplication
)
from PySide6.QtGui import QFont, QIcon


class StartScreen(QWidget):
    """Стартовый экран с выбором режима работы"""
    
    mode_selected = Signal(str)  # 'eco' или 'configurator'
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(30)
        
        # Заголовок
        title = QLabel("🌿 ECOLOGY-BI")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 48px;
            font-weight: bold;
            color: #1F4E79;
            padding: 20px;
        """)
        layout.addWidget(title)
        
        subtitle = QLabel("Экологический мониторинг и аналитика данных")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 18px; color: #666;")
        layout.addWidget(subtitle)
        
        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #ddd; max-width: 400px; margin: 20px auto;")
        layout.addWidget(line)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(40)
        buttons_layout.setAlignment(Qt.AlignCenter)
        
        # Кнопка "Экологический дашборд"
        eco_btn = self._create_mode_button(
            "🌿",
            "Экологический дашборд",
            "Готовый дашборд с KPI, графиками\nи аналитикой обращений",
            "#1F4E79"
        )
        eco_btn.clicked.connect(lambda: self.mode_selected.emit('eco'))
        buttons_layout.addWidget(eco_btn)
        
        # Кнопка "Конфигуратор"
        config_btn = self._create_mode_button(
            "🛠️",
            "Конфигуратор дашбордов",
            "Создай свой дашборд с нуля:\nграфики, текст, фигуры, фильтры",
            "#0078d4"
        )
        config_btn.clicked.connect(lambda: self.mode_selected.emit('configurator'))
        buttons_layout.addWidget(config_btn)
        
        layout.addLayout(buttons_layout)
        
        # Версия
        version = QLabel("Версия 2.0 · Ecology-BI")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("color: #999; font-size: 12px; margin-top: 40px;")
        layout.addWidget(version)
    
    def _create_mode_button(self, icon: str, title: str, description: str, color: str) -> QPushButton:
        """Создаёт кнопку выбора режима"""
        btn = QPushButton()
        btn.setFixedSize(320, 220)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 16px;
                padding: 20px;
                text-align: left;
            }}
            QPushButton:hover {{
                border-color: {color};
                background-color: #f5f8fa;
            }}
        """)
        
        layout = QVBoxLayout(btn)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)
        
        # Иконка
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label)
        
        # Заголовок
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {color};
        """)
        layout.addWidget(title_label)
        
        # Описание
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 13px; color: #666;")
        layout.addWidget(desc_label)
        
        return btn