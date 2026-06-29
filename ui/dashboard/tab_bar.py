from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, 
    QMenu, QInputDialog, QMessageBox
)
from PySide6.QtGui import QAction
from typing import List


class TabBar(QWidget):
    """Панель вкладок для переключения между дашбордами"""
    
    tab_changed = Signal(int)
    tab_added = Signal(str)
    tab_renamed = Signal(int, str)
    tab_closed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(2)
        
        self.tabs = []
        self.current_index = -1
        
        # Кнопка добавления
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(30, 28)
        self.add_btn.setToolTip("Add new dashboard")
        self.add_btn.clicked.connect(self._on_add_clicked)
        
        self.layout.addWidget(self.add_btn)
        self.layout.addStretch()
        
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton.tab-button {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px 4px 0 0;
                padding: 6px 12px;
                min-width: 80px;
            }
            QPushButton.tab-button.active {
                background-color: #0078d4;
                color: white;
                border-color: #0078d4;
            }
            QPushButton.tab-button:hover {
                background-color: #e0e0e0;
            }
            QPushButton.tab-button.active:hover {
                background-color: #005a9e;
            }
            QPushButton.close-btn {
                background-color: transparent;
                border: none;
                padding: 2px 4px;
                font-size: 14px;
                color: #666;
            }
            QPushButton.close-btn:hover {
                background-color: #ff4444;
                color: white;
                border-radius: 3px;
            }
        """)
    
    def set_tabs(self, names: List[str], current: int):
        """Устанавливает список вкладок"""
        self.clear_tabs()
        
        for i, name in enumerate(names):
            self.add_tab_button(name, i == current)
        
        self.current_index = current
    
    def add_tab_button(self, name: str, active: bool = False):
        """Добавляет кнопку вкладки"""
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(2, 2, 2, 2)
        container_layout.setSpacing(2)
        
        btn = QPushButton(name)
        btn.setObjectName(f"tab_{len(self.tabs)}")
        btn.setProperty("class", "tab-button")
        if active:
            btn.setProperty("class", "tab-button active")
        
        btn.clicked.connect(lambda checked, idx=len(self.tabs): 
                           self._on_tab_clicked(idx))
        btn.setContextMenuPolicy(Qt.CustomContextMenu)
        btn.customContextMenuRequested.connect(
            lambda pos, idx=len(self.tabs): self._show_context_menu(pos, idx)
        )
        
        container_layout.addWidget(btn)
        
        close_btn = QPushButton("×")
        close_btn.setObjectName("close-btn")
        close_btn.setFixedSize(18, 18)
        close_btn.setToolTip("Close dashboard")
        close_btn.clicked.connect(lambda checked, idx=len(self.tabs): 
                                  self._on_close_clicked(idx))
        
        container_layout.addWidget(close_btn)
        
        self.layout.insertWidget(len(self.tabs), container)
        self.tabs.append(container)
        
        self._update_active_style()
    
    def clear_tabs(self):
        """Очищает все вкладки"""
        for container in self.tabs:
            self.layout.removeWidget(container)
            container.deleteLater()
        self.tabs.clear()
        self.current_index = -1
    
    def _update_active_style(self):
        """Обновляет стиль активной вкладки"""
        for i, container in enumerate(self.tabs):
            btn = container.findChild(QPushButton, f"tab_{i}")
            if btn:
                if i == self.current_index:
                    btn.setProperty("class", "tab-button active")
                else:
                    btn.setProperty("class", "tab-button")
                btn.style().polish(btn)
    
    def _on_tab_clicked(self, index: int):
        """Обработка клика по вкладке"""
        if index != self.current_index:
            self.current_index = index
            self._update_active_style()
            self.tab_changed.emit(index)
    
    def _on_add_clicked(self):
        """Обработка добавления новой вкладки"""
        name, ok = QInputDialog.getText(
            self, "New Dashboard", "Enter dashboard name:"
        )
        if ok and name:
            self.tab_added.emit(name)
    
    def _on_close_clicked(self, index: int):
        """Обработка закрытия вкладки"""
        if len(self.tabs) <= 1:
            QMessageBox.information(
                self, "Cannot Close", 
                "Cannot close the last dashboard. Create a new one first."
            )
            return
        
        self.tab_closed.emit(index)
    
    def _show_context_menu(self, pos, index: int):
        """Показывает контекстное меню для вкладки"""
        menu = QMenu(self)
        
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self._rename_tab(index))
        menu.addAction(rename_action)
        
        menu.exec(self.tabs[index].mapToGlobal(pos))
    
    def _rename_tab(self, index: int):
        """Переименовывает вкладку"""
        container = self.tabs[index]
        btn = container.findChild(QPushButton, f"tab_{index}")
        if btn:
            old_name = btn.text()
            name, ok = QInputDialog.getText(
                self, "Rename Dashboard", 
                "Enter new name:", text=old_name
            )
            if ok and name and name != old_name:
                btn.setText(name)
                self.tab_renamed.emit(index, name)
    
    def set_active_tab(self, index: int):
        """Устанавливает активную вкладку"""
        if 0 <= index < len(self.tabs):
            self.current_index = index
            self._update_active_style()
    
    def get_tab_name(self, index: int) -> str:
        """Возвращает имя вкладки"""
        if 0 <= index < len(self.tabs):
            container = self.tabs[index]
            btn = container.findChild(QPushButton, f"tab_{index}")
            if btn:
                return btn.text()
        return ""
    
    def update_tab_name(self, index: int, name: str):
        """Обновляет имя вкладки"""
        if 0 <= index < len(self.tabs):
            container = self.tabs[index]
            btn = container.findChild(QPushButton, f"tab_{index}")
            if btn:
                btn.setText(name)