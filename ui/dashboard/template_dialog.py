from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem,
    QLineEdit, QTextEdit, QMessageBox, QFileDialog
)
from PySide6.QtGui import QFont


class TemplateDialog(QDialog):
    """Диалог для управления шаблонами"""
    
    template_applied = Signal(str)
    
    def __init__(self, templates, parent=None):
        super().__init__(parent)
        self.templates = templates
        self.setWindowTitle("Dashboard Templates")
        self.resize(600, 500)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Заголовок
        title = QLabel("📋 Dashboard Templates")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Список шаблонов
        layout.addWidget(QLabel("Available Templates:"))
        
        self.template_list = QListWidget()
        self.template_list.itemSelectionChanged.connect(self.on_template_selected)
        
        for template in self.templates:
            item = QListWidgetItem(f"📊 {template['name']}")
            item.setData(Qt.UserRole, template)
            self.template_list.addItem(item)
        
        layout.addWidget(self.template_list)
        
        # Описание шаблона
        layout.addWidget(QLabel("Description:"))
        self.description_label = QLabel("Select a template to view description")
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("padding: 8px; background: #f5f5f5; border-radius: 4px;")
        layout.addWidget(self.description_label)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton("✅ Apply Template")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self.apply_template)
        
        self.save_btn = QPushButton("💾 Save Current as Template")
        self.save_btn.clicked.connect(self.save_template)
        
        self.delete_btn = QPushButton("🗑️ Delete Template")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_template)
        
        buttons_layout.addWidget(self.apply_btn)
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.delete_btn)
        
        layout.addLayout(buttons_layout)
        
        # Кнопка закрытия
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)
    
    def on_template_selected(self):
        """Обработчик выбора шаблона"""
        items = self.template_list.selectedItems()
        if items:
            template = items[0].data(Qt.UserRole)
            self.description_label.setText(template.get("description", "No description"))
            self.apply_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
        else:
            self.description_label.setText("Select a template to view description")
            self.apply_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
    
    def apply_template(self):
        """Применяет выбранный шаблон"""
        items = self.template_list.selectedItems()
        if items:
            template = items[0].data(Qt.UserRole)
            self.template_applied.emit(template["filename"])
            self.accept()
    
    def save_template(self):
        """Сохраняет текущий дашборд как шаблон"""
        # Запрашиваем название и описание
        from PySide6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(
            self, "Save Template", 
            "Enter template name:"
        )
        if not ok or not name:
            return
        
        description, ok = QInputDialog.getText(
            self, "Save Template",
            "Enter template description:"
        )
        if not ok:
            return
        
        # Возвращаем данные для сохранения
        self.parent().save_current_as_template(name, description)
        self.accept()
    
    def delete_template(self):
        """Удаляет выбранный шаблон"""
        items = self.template_list.selectedItems()
        if not items:
            return
        
        template = items[0].data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, "Delete Template",
            f"Are you sure you want to delete '{template['name']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            from core.template_manager import TemplateManager
            TemplateManager.delete_template(template["filename"])
            # Обновляем список
            self.parent().refresh_templates()
            self.accept()