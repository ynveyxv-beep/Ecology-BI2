from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QCursor
from PySide6.QtWidgets import QGraphicsProxyWidget, QWidget, QVBoxLayout, QLabel


class ShapeItem(QGraphicsProxyWidget):
    """Геометрическая фигура для дашборда"""
    
    RESIZE_NONE = 0
    RESIZE_TOP_LEFT = 1
    RESIZE_TOP = 2
    RESIZE_TOP_RIGHT = 3
    RESIZE_RIGHT = 4
    RESIZE_BOTTOM_RIGHT = 5
    RESIZE_BOTTOM = 6
    RESIZE_BOTTOM_LEFT = 7
    RESIZE_LEFT = 8
    
    SHAPE_RECTANGLE = "rectangle"
    SHAPE_CIRCLE = "circle"
    SHAPE_LINE = "line"
    SHAPE_ARROW = "arrow"
    
    def __init__(
        self,
        shape_type="rectangle",
        width=200,
        height=150,
        color="#0078d4",
        fill_color="#e6f2ff",  # Светло-синий по умолчанию
        line_width=2,
        corner_radius=8,
    ):
        super().__init__()
        
        # Настройки для QGraphicsScene
        self.setFlag(QGraphicsProxyWidget.ItemIsMovable, True)
        self.setFlag(QGraphicsProxyWidget.ItemIsSelectable, True)
        self.setFlag(QGraphicsProxyWidget.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsProxyWidget.ItemIsFocusable, True)
        
        self.setAcceptHoverEvents(True)
        self.setAcceptTouchEvents(True)
        
        # Сохраняем данные
        self.shape_type = shape_type
        self.color = color
        self.fill_color = fill_color
        self.line_width = line_width
        self.corner_radius = corner_radius
        self.chart_type = "shape"
        
        # Размеры
        self.chart_width = width
        self.chart_height = height
        
        # Параметры изменения размера
        self._resize_mode = self.RESIZE_NONE
        self._resize_start_pos = None
        self._resize_start_rect = None
        self._handle_size = 12
        self._min_width = 20
        self._min_height = 20
        
        # Флаг для перемещения
        self._is_dragging = False
        self._drag_start_pos = None
        self._drag_start_item_pos = None
        
        # Создаём виджет-заглушку (будем рисовать сами)
        self.shape_widget = QWidget()
        self.shape_widget.setMinimumSize(width, height)
        self.shape_widget.setAttribute(Qt.WA_TranslucentBackground)  # Прозрачный фон
        
        # Сохраняем ссылку на метод paintEvent
        self.shape_widget.paintEvent = self._paint_shape
        
        self.setWidget(self.shape_widget)
        self.resize(width, height)
    
    def _paint_shape(self, event):
        """Рисует фигуру"""
        painter = QPainter(self.shape_widget)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        rect = self.shape_widget.rect()
        
        # Настройка пера (контур)
        pen = QPen(QColor(self.color))
        pen.setWidth(self.line_width)
        painter.setPen(pen)
        
        # Настройка заливки
        if self.fill_color:
            painter.setBrush(QBrush(QColor(self.fill_color)))
        else:
            painter.setBrush(Qt.NoBrush)
        
        # Рисуем фигуру с отступом для пера
        margin = self.line_width // 2
        draw_rect = rect.adjusted(margin, margin, -margin, -margin)
        
        if self.shape_type == self.SHAPE_RECTANGLE:
            painter.drawRoundedRect(draw_rect, self.corner_radius, self.corner_radius)
        elif self.shape_type == self.SHAPE_CIRCLE:
            painter.drawEllipse(draw_rect)
        elif self.shape_type == self.SHAPE_LINE:
            painter.setBrush(Qt.NoBrush)
            painter.drawLine(margin, self.shape_widget.height()//2,
                           self.shape_widget.width() - margin, self.shape_widget.height()//2)
        elif self.shape_type == self.SHAPE_ARROW:
            painter.setBrush(Qt.NoBrush)
            # Рисуем стрелку
            end_x = self.shape_widget.width() - margin - 15
            mid_y = self.shape_widget.height() // 2
            
            # Линия
            painter.drawLine(margin, mid_y, end_x, mid_y)
            
            # Наконечник стрелки (с заливкой)
            painter.setBrush(QBrush(QColor(self.color)))
            arrow_points = [
                QPointF(self.shape_widget.width() - margin, mid_y),
                QPointF(self.shape_widget.width() - margin - 15, mid_y - 8),
                QPointF(self.shape_widget.width() - margin - 15, mid_y + 8)
            ]
            painter.drawPolygon(arrow_points)
    
    def set_color(self, color):
        """Устанавливает цвет"""
        self.color = color
        self.shape_widget.update()
    
    def set_fill_color(self, color):
        """Устанавливает цвет заливки"""
        self.fill_color = color
        self.shape_widget.update()
    
    # =========================================================
    # RESIZE
    # =========================================================
    
    def resize(self, width, height):
        try:
            super().resize(width, height)
            self.shape_widget.resize(width, height)
        except:
            pass
    
    # =========================================================
    # BOUNDING RECT
    # =========================================================
    
    def boundingRect(self):
        try:
            rect = super().boundingRect()
            return rect.adjusted(
                -self._handle_size//2,
                -self._handle_size//2,
                self._handle_size//2,
                self._handle_size//2
            )
        except:
            return QRectF(0, 0, self.chart_width + self._handle_size, 
                         self.chart_height + self._handle_size)
    
    # =========================================================
    # RESIZE HANDLES
    # =========================================================
    
    def get_resize_handle_at(self, pos):
        try:
            if not self.isSelected():
                return self.RESIZE_NONE
                
            rect = self.widget().rect() if hasattr(self, 'widget') else QRectF(0, 0, self.chart_width, self.chart_height)
            handle = self._handle_size
            
            if pos.x() < handle and pos.y() < handle:
                return self.RESIZE_TOP_LEFT
            if pos.x() < handle and pos.y() > rect.height() - handle:
                return self.RESIZE_BOTTOM_LEFT
            if pos.x() > rect.width() - handle and pos.y() < handle:
                return self.RESIZE_TOP_RIGHT
            if pos.x() > rect.width() - handle and pos.y() > rect.height() - handle:
                return self.RESIZE_BOTTOM_RIGHT
            if pos.x() < handle:
                return self.RESIZE_LEFT
            if pos.x() > rect.width() - handle:
                return self.RESIZE_RIGHT
            if pos.y() < handle:
                return self.RESIZE_TOP
            if pos.y() > rect.height() - handle:
                return self.RESIZE_BOTTOM
            
            return self.RESIZE_NONE
        except:
            return self.RESIZE_NONE
    
    def get_cursor_for_handle(self, handle_type):
        cursors = {
            self.RESIZE_TOP_LEFT: QCursor(Qt.SizeFDiagCursor),
            self.RESIZE_TOP: QCursor(Qt.SizeVerCursor),
            self.RESIZE_TOP_RIGHT: QCursor(Qt.SizeBDiagCursor),
            self.RESIZE_RIGHT: QCursor(Qt.SizeHorCursor),
            self.RESIZE_BOTTOM_RIGHT: QCursor(Qt.SizeFDiagCursor),
            self.RESIZE_BOTTOM: QCursor(Qt.SizeVerCursor),
            self.RESIZE_BOTTOM_LEFT: QCursor(Qt.SizeBDiagCursor),
            self.RESIZE_LEFT: QCursor(Qt.SizeHorCursor),
        }
        return cursors.get(handle_type, QCursor(Qt.ArrowCursor))
    
    # =========================================================
    # HOVER EVENTS
    # =========================================================
    
    def hoverMoveEvent(self, event):
        try:
            if self.isSelected():
                handle = self.get_resize_handle_at(event.pos())
                if handle != self.RESIZE_NONE:
                    self.setCursor(self.get_cursor_for_handle(handle))
                else:
                    self.setCursor(QCursor(Qt.ArrowCursor))
            else:
                self.setCursor(QCursor(Qt.ArrowCursor))
            
            super().hoverMoveEvent(event)
        except:
            pass
    
    # =========================================================
    # MOUSE EVENTS
    # =========================================================
    
    def mousePressEvent(self, event):
        if not self.isSelected():
            self.setSelected(True)
        
        handle = self.get_resize_handle_at(event.pos())
        if handle != self.RESIZE_NONE:
            self._resize_mode = handle
            self._resize_start_pos = event.scenePos()
            self._resize_start_rect = QRectF(
                self.pos().x(),
                self.pos().y(),
                self.chart_width,
                self.chart_height
            )
            event.accept()
            return
        
        self._is_dragging = True
        self._drag_start_pos = event.scenePos()
        self._drag_start_item_pos = self.pos()
        event.accept()
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self._resize_mode != self.RESIZE_NONE and self._resize_start_pos is not None:
            delta = event.scenePos() - self._resize_start_pos
            
            rect = self._resize_start_rect
            x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
            
            if self._resize_mode in [self.RESIZE_TOP_LEFT, self.RESIZE_LEFT, self.RESIZE_BOTTOM_LEFT]:
                new_w = max(self._min_width, w - delta.x())
                x = x + (w - new_w)
                w = new_w
            
            if self._resize_mode in [self.RESIZE_TOP_RIGHT, self.RESIZE_RIGHT, self.RESIZE_BOTTOM_RIGHT]:
                w = max(self._min_width, w + delta.x())
            
            if self._resize_mode in [self.RESIZE_TOP_LEFT, self.RESIZE_TOP, self.RESIZE_TOP_RIGHT]:
                new_h = max(self._min_height, h - delta.y())
                y = y + (h - new_h)
                h = new_h
            
            if self._resize_mode in [self.RESIZE_BOTTOM_LEFT, self.RESIZE_BOTTOM, self.RESIZE_BOTTOM_RIGHT]:
                h = max(self._min_height, h + delta.y())
            
            self.setPos(x, y)
            self.chart_width = int(w)
            self.chart_height = int(h)
            self.resize(int(w), int(h))
            
            event.accept()
            return
        
        if self._is_dragging and self._drag_start_pos is not None:
            delta = event.scenePos() - self._drag_start_pos
            new_pos = self._drag_start_item_pos + delta
            
            self.setPos(new_pos.x(), new_pos.y())
            
            event.accept()
            return
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if self._resize_mode != self.RESIZE_NONE:
            self._resize_mode = self.RESIZE_NONE
            self._resize_start_pos = None
            self._resize_start_rect = None
            event.accept()
            return
        
        if self._is_dragging:
            self._is_dragging = False
            self._drag_start_pos = None
            self._drag_start_item_pos = None
            event.accept()
            return
        
        super().mouseReleaseEvent(event)
    
    # =========================================================
    # PAINT
    # =========================================================
    
    def paint(self, painter: QPainter, option, widget=None):
        try:
            super().paint(painter, option, widget)

            if self.isSelected():
                rect = self.widget().rect() if hasattr(self, 'widget') else QRectF(0, 0, self.chart_width, self.chart_height)
                
                pen = QPen(QColor(0, 120, 215))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawRect(rect)
                
                handle = self._handle_size
                half = handle // 2
                
                handles = [
                    (0, 0),
                    (rect.width()//2 - half, 0),
                    (rect.width() - handle, 0),
                    (rect.width() - handle, rect.height()//2 - half),
                    (rect.width() - handle, rect.height() - handle),
                    (rect.width()//2 - half, rect.height() - handle),
                    (0, rect.height() - handle),
                    (0, rect.height()//2 - half),
                ]
                
                for hx, hy in handles:
                    painter.setBrush(QBrush(QColor(0, 120, 215)))
                    painter.setPen(QPen(QColor(0, 120, 215), 1))
                    painter.drawRect(QRectF(hx, hy, handle, handle))
        except:
            pass
    
    # =========================================================
    # KEY EVENTS
    # =========================================================
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            if self.scene():
                self.scene().removeItem(self)
            return
        super().keyPressEvent(event)
    
    # =========================================================
    # EXPORT
    # =========================================================
    
    def export_to_png(self, path, scale=2):
        try:
            self.widget().grab().save(path)
            print(f"✅ Exported to {path}")
        except Exception as e:
            print(f"❌ Export error: {e}")