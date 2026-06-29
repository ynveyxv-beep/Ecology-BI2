from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QCursor
from PySide6.QtWidgets import QGraphicsProxyWidget, QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView

import folium
import pandas as pd
import io
import tempfile
import os


class MapItem(QGraphicsProxyWidget):
    """График с картой на основе Folium"""
    
    RESIZE_NONE = 0
    RESIZE_TOP_LEFT = 1
    RESIZE_TOP = 2
    RESIZE_TOP_RIGHT = 3
    RESIZE_RIGHT = 4
    RESIZE_BOTTOM_RIGHT = 5
    RESIZE_BOTTOM = 6
    RESIZE_BOTTOM_LEFT = 7
    RESIZE_LEFT = 8
    
    def __init__(
        self,
        dataframe,
        x_column,
        y_column,
        title="",
        width=600,
        height=400,
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
        self.df = dataframe
        self.x_column = x_column  # Долгота
        self.y_column = y_column  # Широта
        self.title = title
        self.chart_type = "map"
        
        # Размеры
        self.chart_width = width
        self.chart_height = height
        
        # Параметры изменения размера
        self._resize_mode = self.RESIZE_NONE
        self._resize_start_pos = None
        self._resize_start_rect = None
        self._handle_size = 12
        self._min_width = 200
        self._min_height = 150
        
        # Флаг для перемещения
        self._is_dragging = False
        self._drag_start_pos = None
        self._drag_start_item_pos = None
        
        # Создаём виджет с картой
        self.map_widget = QWidget()
        self.map_layout = QVBoxLayout(self.map_widget)
        self.map_layout.setContentsMargins(0, 0, 0, 0)
        
        self.web_view = QWebEngineView()
        self.map_layout.addWidget(self.web_view)
        
        self.setWidget(self.map_widget)
        self.resize(width, height)
        
        # Строим карту
        self.build_map()
    
    # =========================================================
    # BUILD MAP
    # =========================================================
    
    def build_map(self):
        """Строит карту с данными"""
        try:
            # Проверяем наличие данных
            if self.df is None or self.df.empty:
                self._show_message("No data available")
                return
            
            # Проверяем колонки
            if self.x_column not in self.df.columns:
                self._show_message(f"Column '{self.x_column}' not found")
                return
            
            if self.y_column not in self.df.columns:
                self._show_message(f"Column '{self.y_column}' not found")
                return
            
            # Получаем координаты
            lat = self.df[self.y_column].values
            lon = self.df[self.x_column].values
            
            # Удаляем NaN
            mask = pd.notna(lat) & pd.notna(lon)
            lat = lat[mask]
            lon = lon[mask]
            
            if len(lat) == 0:
                self._show_message("No valid coordinates")
                return
            
            # Вычисляем центр карты
            center_lat = float(lat.mean())
            center_lon = float(lon.mean())
            
            # Создаём карту
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=10,
                tiles='OpenStreetMap',
                width='100%',
                height='100%'
            )
            
            # Добавляем маркеры
            for i in range(len(lat)):
                folium.Marker(
                    location=[float(lat[i]), float(lon[i])],
                    popup=f"Lat: {lat[i]:.4f}, Lon: {lon[i]:.4f}",
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)
            
            # Добавляем заголовок
            if self.title:
                folium.TileLayer(
                    tiles='OpenStreetMap',
                    name=self.title
                ).add_to(m)
            
            # Сохраняем в HTML
            html = m.get_root().render()
            
            # Встраиваем в WebView
            self.web_view.setHtml(html)
            
        except Exception as e:
            print(f"❌ Map error: {e}")
            self._show_message(f"Error: {str(e)}")
    
    def _show_message(self, message):
        """Показывает сообщение на карте"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    font-family: Arial;
                    color: #666;
                    background: #f5f5f5;
                    margin: 0;
                }}
                .message {{
                    text-align: center;
                    padding: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="message">{message}</div>
        </body>
        </html>
        """
        self.web_view.setHtml(html)
    
    # =========================================================
    # RESIZE
    # =========================================================
    
    def resize(self, width, height):
        try:
            super().resize(width, height)
            self.map_widget.resize(width, height)
        except:
            pass
    
    # =========================================================
    # BOUNDING RECT
    # =========================================================
    
    def boundingRect(self):
        try:
            rect = super().boundingRect()
            return rect.adjusted(
                -self._handle_size/2,
                -self._handle_size/2,
                self._handle_size/2,
                self._handle_size/2
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
                half = handle / 2
                
                handles = [
                    (0, 0),
                    (rect.width()/2 - half, 0),
                    (rect.width() - handle, 0),
                    (rect.width() - handle, rect.height()/2 - half),
                    (rect.width() - handle, rect.height() - handle),
                    (rect.width()/2 - half, rect.height() - handle),
                    (0, rect.height() - handle),
                    (0, rect.height()/2 - half),
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
        """Экспортирует карту в PNG (через screenshot)"""
        try:
            # Делаем скриншот WebView
            self.web_view.grab().save(path)
            print(f"✅ Exported to {path}")
        except Exception as e:
            print(f"❌ Export error: {e}")