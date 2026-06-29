from PySide6.QtCore import Qt, QPoint, QRectF, QLineF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsSceneMouseEvent


class GridCanvas(QGraphicsView):
    """Canvas с сеткой, Snap to Grid и линиями выравнивания"""
    
    def __init__(self, grid_size=20):
        super().__init__()
        
        self.grid_size = grid_size
        self.snap_enabled = True
        self._alignment_lines = []
        self._alignment_threshold = 15
        self._drag_item = None
        
        # Создаём сцену
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Начальный размер сцены (будет динамически меняться)
        self.scene.setSceneRect(0, 0, 1000, 800)
        
        # Настройки отображения
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # Фон с сеткой
        self.setBackgroundBrush(QColor(240, 240, 240))
        
        # Панорамирование
        self._panning = False
        self._pan_start = None
    
    # =========================================================
    # DYNAMIC SCENE SIZE
    # =========================================================
    
    def update_scene_size(self):
        """Обновляет размер сцены в зависимости от содержимого"""
        items = self.scene.items()
        
        if not items:
            # Если нет элементов, устанавливаем минимальный размер
            self.scene.setSceneRect(0, 0, 1000, 800)
            return
        
        # Находим максимальные координаты элементов
        max_x = 0
        max_y = 0
        
        for item in items:
            if hasattr(item, 'x') and hasattr(item, 'y'):
                # Получаем позицию элемента
                item_x = item.x() + 50  # Отступ справа
                item_y = item.y() + 50  # Отступ снизу
                
                # Учитываем размер элемента
                if hasattr(item, 'boundingRect'):
                    rect = item.boundingRect()
                    item_x += rect.width()
                    item_y += rect.height()
                elif hasattr(item, 'width') and hasattr(item, 'height'):
                    item_x += item.width()
                    item_y += item.height()
                
                if item_x > max_x:
                    max_x = item_x
                if item_y > max_y:
                    max_y = item_y
        
        # Добавляем отступы
        new_width = max(max_x + 100, 1000)
        new_height = max(max_y + 100, 800)
        
        # Устанавливаем новый размер сцены
        self.scene.setSceneRect(0, 0, new_width, new_height)
    
    # =========================================================
    # DRAW GRID
    # =========================================================
    
    def drawBackground(self, painter: QPainter, rect: QRectF):
        """Рисует сетку и линии выравнивания на фоне"""
        super().drawBackground(painter, rect)
        
        if self.snap_enabled:
            self._draw_grid(painter, rect)
        
        self._draw_alignment_lines(painter, rect)
    
    def _draw_grid(self, painter: QPainter, rect: QRectF):
        """Рисует сетку"""
        view_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        transform = self.transform()
        scale = transform.m11()
        
        grid_size = self.grid_size
        if scale < 0.5:
            grid_size = self.grid_size * 4
        elif scale < 1.0:
            grid_size = self.grid_size * 2
        
        alpha = min(255, max(50, int(255 * scale)))
        
        pen = QPen(QColor(200, 200, 200, alpha))
        pen.setWidth(1)
        painter.setPen(pen)
        
        start_x = int(view_rect.left() / grid_size) * grid_size
        end_x = int(view_rect.right() / grid_size) * grid_size + grid_size
        for x in range(start_x, end_x, int(grid_size)):
            painter.drawLine(x, view_rect.top(), x, view_rect.bottom())
        
        start_y = int(view_rect.top() / grid_size) * grid_size
        end_y = int(view_rect.bottom() / grid_size) * grid_size + grid_size
        for y in range(start_y, end_y, int(grid_size)):
            painter.drawLine(view_rect.left(), y, view_rect.right(), y)
        
        bold_pen = QPen(QColor(180, 180, 180, alpha))
        bold_pen.setWidth(1)
        painter.setPen(bold_pen)
        
        big_grid = grid_size * 5
        start_x = int(view_rect.left() / big_grid) * big_grid
        end_x = int(view_rect.right() / big_grid) * big_grid + big_grid
        for x in range(start_x, end_x, int(big_grid)):
            painter.drawLine(x, view_rect.top(), x, view_rect.bottom())
        
        start_y = int(view_rect.top() / big_grid) * big_grid
        end_y = int(view_rect.bottom() / big_grid) * big_grid + big_grid
        for y in range(start_y, end_y, int(big_grid)):
            painter.drawLine(view_rect.left(), y, view_rect.right(), y)
    
    def _draw_alignment_lines(self, painter: QPainter, rect: QRectF):
        """Рисует линии выравнивания"""
        if not self._alignment_lines:
            return
        
        pen = QPen(QColor(255, 0, 0, 150))
        pen.setWidth(1)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        
        for line in self._alignment_lines:
            painter.drawLine(line)
    
    # =========================================================
    # SNAP TO GRID
    # =========================================================
    
    def snap_to_grid(self, pos: QPoint) -> QPoint:
        if not self.snap_enabled:
            return pos
        
        x = round(pos.x() / self.grid_size) * self.grid_size
        y = round(pos.y() / self.grid_size) * self.grid_size
        
        return QPoint(x, y)
    
    # =========================================================
    # ALIGNMENT LINES
    # =========================================================
    
    def update_alignment_lines(self, item):
        self._alignment_lines.clear()
        
        if not item:
            return
        
        item_x = item.x()
        item_y = item.y()
        item_rect = item.boundingRect() if hasattr(item, 'boundingRect') else QRectF(0, 0, 100, 100)
        item_width = item_rect.width()
        item_height = item_rect.height()
        
        item_points = {
            'left': item_x,
            'right': item_x + item_width,
            'center_x': item_x + item_width / 2,
            'top': item_y,
            'bottom': item_y + item_height,
            'center_y': item_y + item_height / 2
        }
        
        for other_item in self.scene.items():
            if other_item == item:
                continue
            
            if not hasattr(other_item, 'x') or not hasattr(other_item, 'y'):
                continue
            
            if not other_item.isVisible():
                continue
            
            other_x = other_item.x()
            other_y = other_item.y()
            other_rect = other_item.boundingRect() if hasattr(other_item, 'boundingRect') else QRectF(0, 0, 100, 100)
            other_width = other_rect.width()
            other_height = other_rect.height()
            
            other_points = {
                'left': other_x,
                'right': other_x + other_width,
                'center_x': other_x + other_width / 2,
                'top': other_y,
                'bottom': other_y + other_height,
                'center_y': other_y + other_height / 2
            }
            
            for key in ['left', 'right', 'center_x']:
                if abs(item_points[key] - other_points[key]) < self._alignment_threshold:
                    x = other_points[key]
                    self._alignment_lines.append(
                        QLineF(x, item_y - 50, x, item_y + item_height + 50)
                    )
                    if key == 'left':
                        item.setX(other_points[key])
                    elif key == 'right':
                        item.setX(other_points[key] - item_width)
                    elif key == 'center_x':
                        item.setX(other_points[key] - item_width / 2)
                    break
            
            for key in ['top', 'bottom', 'center_y']:
                if abs(item_points[key] - other_points[key]) < self._alignment_threshold:
                    y = other_points[key]
                    self._alignment_lines.append(
                        QLineF(item_x - 50, y, item_x + item_width + 50, y)
                    )
                    if key == 'top':
                        item.setY(other_points[key])
                    elif key == 'bottom':
                        item.setY(other_points[key] - item_height)
                    elif key == 'center_y':
                        item.setY(other_points[key] - item_height / 2)
                    break
        
        self.update()
    
    def clear_alignment_lines(self):
        self._alignment_lines.clear()
        self.update()
    
    # =========================================================
    # MOUSE EVENTS
    # =========================================================
    
    def mousePressEvent(self, event):
        # Проверяем, кликнули ли по элементу
        item = self.itemAt(event.pos())
        
        # Если клик по пустому месту — очищаем линии
        if event.button() == Qt.LeftButton and not item:
            self.clear_alignment_lines()
        
        # Если клик по элементу
        if item and isinstance(item, QGraphicsItem):
            # Если это PlotItem или его потомок
            if hasattr(item, 'setPos') or hasattr(item, 'x'):
                self._drag_item = item
        
        # Если это PlotItem, передаём событие ему
        if item and hasattr(item, 'plot_widget'):
            # Преобразуем событие для PlotItem
            scene_pos = self.mapToScene(event.pos())
            click_event = QGraphicsSceneMouseEvent()
            click_event.setPos(scene_pos)
            click_event.setScenePos(scene_pos)
            click_event.setButton(event.button())
            click_event.setButtons(event.buttons())
            click_event.setModifiers(event.modifiers())
            
            # Передаём событие PlotItem
            item.mousePressEvent(click_event)
            return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        
        if self._drag_item:
            self.update_alignment_lines(self._drag_item)
    
    def mouseReleaseEvent(self, event):
        self._drag_item = None
        self.clear_alignment_lines()
        super().mouseReleaseEvent(event)
        
        # Обновляем размер сцены после перемещения
        self.update_scene_size()
    
    # =========================================================
    # ZOOM
    # =========================================================

    def wheelEvent(self, event):
        zoom = 1.15
        if event.angleDelta().y() > 0:
            self.scale(zoom, zoom)
        else:
            self.scale(1 / zoom, 1 / zoom)
        
        self.clear_alignment_lines()

    # =========================================================
    # MIDDLE MOUSE PANNING
    # =========================================================

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()

            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        super().mouseReleaseEvent(event)

    # =========================================================
    # DELETE SELECTED
    # =========================================================

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            for item in self.scene.selectedItems():
                self.scene.removeItem(item)
            self.clear_alignment_lines()
            # Обновляем размер сцены после удаления
            self.update_scene_size()
            return

        super().keyPressEvent(event)
    
    # =========================================================
    # TOGGLE SNAP
    # =========================================================
    
    def toggle_snap(self):
        self.snap_enabled = not self.snap_enabled
        self.clear_alignment_lines()
        return self.snap_enabled