from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QCursor, QFont, QTextCursor
from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsTextItem, QGraphicsProxyWidget, 
    QWidget, QVBoxLayout, QMenu, QColorDialog, QFontDialog, QInputDialog, QDialog
)


class TextItem(QGraphicsTextItem):
    """Текстовый блок на основе QGraphicsTextItem"""
    
    def __init__(
        self,
        text="",
        text_type="text",
        font_size=14,
        bold=False,
        color="#333333",
        background_color=None,
        width=400,
        height=100,
    ):
        super().__init__()
        
        # Делаем элемент перемещаемым и выбираемым
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        
        # Сохраняем данные
        self.text = text
        self.text_type = text_type
        self.font_size = font_size
        self.bold = bold
        self.color = color
        self.background_color = background_color
        self.chart_type = "text"
        
        # Размеры
        self.chart_width = width
        self.chart_height = height
        
        # Настройка текста
        self.setPlainText(text)
        
        # Настройка шрифта
        font = QFont()
        font.setPointSize(font_size)
        font.setBold(bold)
        self.setFont(font)
        
        # Настройка цвета
        self.setDefaultTextColor(QColor(color))
        
        # Включаем перенос слов и устанавливаем ширину
        self.setTextWidth(width - 20)
        
        # Устанавливаем размер элемента
        self.setPos(0, 0)
        
        # Настройка фона
        self._update_background()
        
        # Контекстное меню
        self.setAcceptHoverEvents(True)
    
    def _update_background(self):
        """Обновляет фон"""
        self.update()
    
    def paint(self, painter, option, widget=None):
        """Рисует текст с фоном"""
        # Рисуем фон
        if self.background_color:
            painter.save()
            painter.setBrush(QBrush(QColor(self.background_color)))
            painter.setPen(QPen(Qt.NoPen))
            rect = self.boundingRect()
            painter.drawRoundedRect(rect, 8, 8)
            painter.restore()
        
        # Рисуем текст
        super().paint(painter, option, widget)
    
    def mouseDoubleClickEvent(self, event):
        """Редактирование при двойном клике"""
        from PySide6.QtWidgets import QTextEdit, QDialog, QVBoxLayout, QDialogButtonBox
        
        # Создаём диалог с QTextEdit
        dialog = QDialog()
        dialog.setWindowTitle("Edit Text")
        dialog.resize(500, 300)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(self.toPlainText())
        layout.addWidget(text_edit)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.Accepted:
            new_text = text_edit.toPlainText()
            if new_text is not None:
                self.text = new_text
                self.setPlainText(new_text)
                # Обновляем размеры
                self._update_size()
    
    def _update_size(self):
        """Обновляет размер элемента после изменения текста"""
        # Получаем bounding rect текста
        rect = self.boundingRect()
        
        # Добавляем отступы
        margin = 20
        new_width = max(rect.width() + margin, self.chart_width)
        new_height = max(rect.height() + margin, self.chart_height)
        
        # Обновляем размеры
        self.chart_width = new_width
        self.chart_height = new_height
        
        # Обновляем ширину текста для переноса
        self.setTextWidth(new_width - 20)
        
        # Уведомляем сцену об изменении
        self.prepareGeometryChange()
        self.update()
    
    def show_context_menu(self, pos):
        """Контекстное меню"""
        menu = QMenu()
        
        bg_action = menu.addAction("🎨 Change Background")
        bg_action.triggered.connect(self.change_background)
        
        color_action = menu.addAction("✏️ Change Text Color")
        color_action.triggered.connect(self.change_color)
        
        font_action = menu.addAction("🔤 Change Font")
        font_action.triggered.connect(self.change_font)
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(self.delete_self)
        
        menu.exec(pos)
    
    def change_background(self):
        """Изменяет цвет фона"""
        color = QColorDialog.getColor(QColor(self.background_color or "#ffffff"))
        if color.isValid():
            self.background_color = color.name()
            self.update()
    
    def change_color(self):
        """Изменяет цвет текста"""
        color = QColorDialog.getColor(QColor(self.color))
        if color.isValid():
            self.color = color.name()
            self.setDefaultTextColor(QColor(color))
    
    def change_font(self):
        """Изменяет шрифт"""
        font, ok = QFontDialog.getFont(self.font())
        if ok:
            self.setFont(font)
            self._update_size()
    
    def delete_self(self):
        """Удаляет элемент"""
        if self.scene():
            self.scene().removeItem(self)
    
    def contextMenuEvent(self, event):
        """Обработка ПКМ"""
        self.show_context_menu(event.screenPos())
        event.accept()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.delete_self()
            return
        super().keyPressEvent(event)
    
    def resize(self, width, height):
        """Изменяет размер"""
        self.chart_width = width
        self.chart_height = height
        self.setTextWidth(width - 20)
        self.prepareGeometryChange()
        self.update()
    
    def export_to_png(self, path, scale=2):
        """Экспорт в PNG"""
        try:
            from PySide6.QtGui import QPixmap, QPainter
            
            # Получаем bounding rect
            rect = self.boundingRect()
            width = int(rect.width() * scale)
            height = int(rect.height() * scale)
            
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.transparent)
            
            painter = QPainter(pixmap)
            painter.scale(scale, scale)
            # Смещаем для правильной позиции
            painter.translate(-rect.x(), -rect.y())
            self.paint(painter, None, None)
            painter.end()
            
            pixmap.save(path)
            print(f"✅ Exported to {path}")
        except Exception as e:
            print(f"❌ Export error: {e}")