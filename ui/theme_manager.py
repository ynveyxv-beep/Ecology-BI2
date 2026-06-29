from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QWidget


class ThemeManager:
    """Управление темами приложения"""
    
    LIGHT = "light"
    DARK = "dark"
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.current_theme = self.LIGHT
        self._main_window = None
        
        # Загружаем сохранённую тему
        self._load_theme()
    
    def set_main_window(self, main_window):
        """Устанавливает главное окно для применения темы"""
        self._main_window = main_window
    
    def get_current_theme(self) -> str:
        """Возвращает текущую тему"""
        return self.current_theme
    
    def toggle_theme(self):
        """Переключает тему"""
        if self.current_theme == self.LIGHT:
            self.set_theme(self.DARK)
        else:
            self.set_theme(self.LIGHT)
    
    def set_theme(self, theme: str):
        """Устанавливает тему"""
        if theme not in [self.LIGHT, self.DARK]:
            return
        
        self.current_theme = theme
        self._save_theme()
        
        if self._main_window:
            self._apply_theme_to_main_window()
            
        # Принудительно обновляем все виджеты
        app = QApplication.instance()
        if app:
            # Обновляем стиль приложения
            app.setStyleSheet(self.get_stylesheet())
            # Обновляем все виджеты
            for widget in app.allWidgets():
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()
    
    def _apply_theme_to_main_window(self):
        """Применяет тему к главному окну"""
        if self.current_theme == self.DARK:
            self._apply_dark_theme()
        else:
            self._apply_light_theme()
    
    def _apply_dark_theme(self):
        """Применяет тёмную тему через QPalette"""
        dark_palette = QPalette()
        
        # Основные цвета
        dark = QColor(53, 53, 53)
        darker = QColor(35, 35, 35)
        lighter = QColor(80, 80, 80)
        text = QColor(220, 220, 220)
        text_light = QColor(200, 200, 200)
        highlight = QColor(42, 130, 218)
        
        dark_palette.setColor(QPalette.Window, dark)
        dark_palette.setColor(QPalette.WindowText, text)
        dark_palette.setColor(QPalette.Base, darker)
        dark_palette.setColor(QPalette.AlternateBase, dark)
        dark_palette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipText, text)
        dark_palette.setColor(QPalette.Text, text)
        dark_palette.setColor(QPalette.Button, dark)
        dark_palette.setColor(QPalette.ButtonText, text)
        dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        dark_palette.setColor(QPalette.Link, highlight)
        dark_palette.setColor(QPalette.Highlight, highlight)
        dark_palette.setColor(QPalette.HighlightedText, Qt.white)
        dark_palette.setColor(QPalette.PlaceholderText, QColor(150, 150, 150))
        
        if self._main_window:
            self._main_window.setPalette(dark_palette)
            # Применяем ко всем дочерним виджетам
            for widget in self._main_window.findChildren(QWidget):
                widget.setPalette(dark_palette)
    
    def _apply_light_theme(self):
        """Применяет светлую тему"""
        if self._main_window:
            # Сбрасываем палитру на системную
            self._main_window.setPalette(self._main_window.style().standardPalette())
            for widget in self._main_window.findChildren(QWidget):
                widget.setPalette(self._main_window.style().standardPalette())
    
    def get_stylesheet(self) -> str:
        """Возвращает CSS стили для текущей темы"""
        if self.current_theme == self.DARK:
            return self._get_dark_stylesheet()
        else:
            return ""
    
    def _get_dark_stylesheet(self) -> str:
        """Возвращает CSS для тёмной темы"""
        return """
            /* Основные цвета */
            QWidget {
                background-color: #2b2b2b;
                color: #dcdcdc;
            }
            
            QMainWindow {
                background-color: #2b2b2b;
            }
            
            QMenuBar {
                background-color: #3c3c3c;
                color: #dcdcdc;
            }
            QMenuBar::item:selected {
                background-color: #4a4a4a;
            }
            QMenu {
                background-color: #3c3c3c;
                color: #dcdcdc;
                border: 1px solid #4a4a4a;
            }
            QMenu::item:selected {
                background-color: #4a4a4a;
            }
            
            QDockWidget {
                background-color: #2b2b2b;
                color: #dcdcdc;
            }
            QDockWidget::title {
                background-color: #3c3c3c;
                color: #dcdcdc;
                padding: 5px;
            }
            
            QPushButton {
                background-color: #3c3c3c;
                color: #dcdcdc;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QPushButton:disabled {
                color: #666666;
            }
            
            QPushButton#loadBtn {
                background-color: #0078d4;
                color: white;
                border: none;
            }
            QPushButton#loadBtn:hover {
                background-color: #005a9e;
            }
            
            QComboBox {
                background-color: #3c3c3c;
                color: #dcdcdc;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox:hover {
                border-color: #5a5a5a;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                color: #dcdcdc;
                selection-background-color: #4a4a4a;
            }
            
            QLineEdit {
                background-color: #3c3c3c;
                color: #dcdcdc;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 5px;
            }
            
            QTableWidget {
                background-color: #2b2b2b;
                color: #dcdcdc;
                gridline-color: #3c3c3c;
                border: 1px solid #4a4a4a;
            }
            QTableWidget::item:selected {
                background-color: #4a4a4a;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                color: #dcdcdc;
                padding: 5px;
                border: 1px solid #4a4a4a;
            }
            
            QTabWidget::pane {
                border: 1px solid #4a4a4a;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #dcdcdc;
                padding: 8px 16px;
                border: 1px solid #4a4a4a;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #4a4a4a;
            }
            QTabBar::tab:hover:!selected {
                background-color: #454545;
            }
            
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 12px;
                border: 1px solid #3c3c3c;
            }
            QScrollBar::handle:vertical {
                background-color: #5a5a5a;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6a6a6a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            
            QScrollBar:horizontal {
                background-color: #2b2b2b;
                height: 12px;
                border: 1px solid #3c3c3c;
            }
            QScrollBar::handle:horizontal {
                background-color: #5a5a5a;
                min-width: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #6a6a6a;
            }
            
            QGroupBox {
                color: #dcdcdc;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            
            QLabel {
                color: #dcdcdc;
            }
            
            QCheckBox {
                color: #dcdcdc;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                background-color: #3c3c3c;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border-color: #0078d4;
            }
            
            QToolBar {
                background-color: #3c3c3c;
                border: none;
                spacing: 3px;
                padding: 3px;
            }
            QToolBar QToolButton {
                background-color: transparent;
                color: #dcdcdc;
                border: none;
                padding: 5px 8px;
                border-radius: 4px;
            }
            QToolBar QToolButton:hover {
                background-color: #4a4a4a;
            }
            QToolBar QToolButton:pressed {
                background-color: #2a2a2a;
            }
            QToolBar QToolButton:checked {
                background-color: #4a4a4a;
            }
            
            QStatusBar {
                background-color: #2b2b2b;
                color: #dcdcdc;
            }
            
            QListWidget {
                background-color: #2b2b2b;
                color: #dcdcdc;
                border: 1px solid #4a4a4a;
            }
            QListWidget::item:selected {
                background-color: #4a4a4a;
            }
            QListWidget::item:hover {
                background-color: #3c3c3c;
            }
            
            QGraphicsView {
                background-color: #2b2b2b;
                border: none;
            }
            
            QDockWidget {
                background-color: #2b2b2b;
            }
            
            /* Текст в таблице */
            QTableWidget QTableWidgetItem {
                color: #dcdcdc;
            }
            
            /* Заголовки колонок */
            QHeaderView {
                background-color: #3c3c3c;
                color: #dcdcdc;
            }
        """
    
    def _save_theme(self):
        """Сохраняет выбранную тему в настройках"""
        settings = QSettings("DashboardBuilder", "Settings")
        settings.setValue("theme", self.current_theme)
    
    def _load_theme(self):
        """Загружает сохранённую тему из настроек"""
        settings = QSettings("DashboardBuilder", "Settings")
        theme = settings.value("theme", self.LIGHT)
        if theme in [self.LIGHT, self.DARK]:
            self.current_theme = theme