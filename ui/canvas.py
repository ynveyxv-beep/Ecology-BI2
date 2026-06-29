from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QGraphicsScene,
    QGraphicsView,
)


class Canvas(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Большое рабочее поле
        self.scene.setSceneRect(0, 0, 5000, 5000)

        # Настройки отображения
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)

        self.setDragMode(QGraphicsView.RubberBandDrag)

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        self.setBackgroundBrush(Qt.lightGray)

        # Панорамирование
        self._panning = False
        self._pan_start = None

    # ======================================================
    # Zoom
    # ======================================================

    def wheelEvent(self, event):
        zoom = 1.15

        if event.angleDelta().y() > 0:
            self.scale(zoom, zoom)
        else:
            self.scale(1 / zoom, 1 / zoom)

    # ======================================================
    # Middle mouse panning
    # ======================================================

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

    # ======================================================
    # Delete selected charts
    # ======================================================

    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Delete:
            for item in self.scene.selectedItems():
                self.scene.removeItem(item)
            return

        super().keyPressEvent(event)