from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, 
    QMenu, QInputDialog, QMessageBox
)
from PySide6.QtGui import QAction
from typing import List


class PageTabBar(QWidget):
    """Панель вкладок для переключения между страницами внутри дашборда"""
    
    page_changed = Signal(int)
    page_added = Signal(str)
    page_renamed = Signal(int, str)
    page_closed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(2)
        
        self.tabs = []
        self.current_index = -1
        
        # Кнопка добавления
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(25, 25)
        self.add_btn.setToolTip("Add new page")
        self.add_btn.clicked.connect(self._on_add_clicked)
        
        self.layout.addWidget(QLabel("📄 Pages:"))
        self.layout.addWidget(self.add_btn)
        self.layout.addStretch()
        
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 2px 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton.page-button {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px 12px;
                min-width: 60px;
                font-size: 11px;
            }
            QPushButton.page-button.active {
                background-color: #0078d4;
                color: white;
                border-color: #0078d4;
            }
            QPushButton.page-button:hover {
                background-color: #e0e0e0;
            }
            QPushButton.page-button.active:hover {
                background-color: #005a9e;
            }
            QPushButton.close-btn {
                background-color: transparent;
                border: none;
                padding: 0px 4px;
                font-size: 14px;
                color: #666;
            }
            QPushButton.close-btn:hover {
                background-color: #ff4444;
                color: white;
                border-radius: 3px;
            }
            QLabel {
                font-size: 11px;
                color: #666;
            }
        """)
    
    def set_pages(self, names: List[str], current: int):
        """Устанавливает список страниц"""
        self.clear_tabs()
        
        for i, name in enumerate(names):
            self.add_page_button(name, i == current)
        
        self.current_index = current
    
    def add_page_button(self, name: str, active: bool = False):
        """Добавляет кнопку страницы"""
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(2, 2, 2, 2)
        container_layout.setSpacing(2)
        
        btn = QPushButton(name)
        btn.setObjectName(f"page_{len(self.tabs)}")
        btn.setProperty("class", "page-button")
        if active:
            btn.setProperty("class", "page-button active")
        
        btn.clicked.connect(lambda checked, idx=len(self.tabs): 
                           self._on_page_clicked(idx))
        btn.setContextMenuPolicy(Qt.CustomContextMenu)
        btn.customContextMenuRequested.connect(
            lambda pos, idx=len(self.tabs): self._show_context_menu(pos, idx)
        )
        
        container_layout.addWidget(btn)
        
        # Кнопка закрытия (только если больше одной страницы)
        close_btn = QPushButton("×")
        close_btn.setObjectName("close-btn")
        close_btn.setFixedSize(16, 16)
        close_btn.setToolTip("Close page")
        close_btn.clicked.connect(lambda checked, idx=len(self.tabs): 
                                  self._on_close_clicked(idx))
        
        container_layout.addWidget(close_btn)
        
        self.layout.insertWidget(len(self.tabs) + 2, container)
        self.tabs.append(container)
        
        self._update_active_style()
    
    def clear_tabs(self):
        """Очищает все страницы"""
        for container in self.tabs:
            self.layout.removeWidget(container)
            container.deleteLater()
        self.tabs.clear()
        self.current_index = -1
    
    def _update_active_style(self):
        """Обновляет стиль активной страницы"""
        for i, container in enumerate(self.tabs):
            btn = container.findChild(QPushButton, f"page_{i}")
            if btn:
                if i == self.current_index:
                    btn.setProperty("class", "page-button active")
                else:
                    btn.setProperty("class", "page-button")
                btn.style().polish(btn)
    
    def _on_page_clicked(self, index: int):
        """Обработка клика по странице"""
        if index != self.current_index:
            self.current_index = index
            self._update_active_style()
            self.page_changed.emit(index)
    
    def _on_add_clicked(self):
        """Обработка добавления новой страницы"""
        name, ok = QInputDialog.getText(
            self, "New Page", "Enter page name:"
        )
        if ok and name:
            self.page_added.emit(name)
    
    def _on_close_clicked(self, index: int):
        """Обработка закрытия страницы"""
        if len(self.tabs) <= 1:
            QMessageBox.information(
                self, "Cannot Close", 
                "Cannot close the last page. Create a new one first."
            )
            return
        
        self.page_closed.emit(index)
    
    def _show_context_menu(self, pos, index: int):
        """Показывает контекстное меню для страницы"""
        menu = QMenu(self)
        
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self._rename_page(index))
        menu.addAction(rename_action)
        
        menu.exec(self.tabs[index].mapToGlobal(pos))
    
    def _rename_page(self, index: int):
        """Переименовывает страницу"""
        container = self.tabs[index]
        btn = container.findChild(QPushButton, f"page_{index}")
        if btn:
            old_name = btn.text()
            name, ok = QInputDialog.getText(
                self, "Rename Page", 
                "Enter new name:", text=old_name
            )
            if ok and name and name != old_name:
                btn.setText(name)
                self.page_renamed.emit(index, name)
    
    def set_active_page(self, index: int):
        """Устанавливает активную страницу"""
        if 0 <= index < len(self.tabs):
            self.current_index = index
            self._update_active_style()
    
    def get_page_name(self, index: int) -> str:
        """Возвращает имя страницы"""
        if 0 <= index < len(self.tabs):
            container = self.tabs[index]
            btn = container.findChild(QPushButton, f"page_{index}")
            if btn:
                return btn.text()
        return ""