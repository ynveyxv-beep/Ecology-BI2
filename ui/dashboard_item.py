from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QGraphicsProxyWidget


class DashboardItem(QGraphicsProxyWidget):

    HANDLE_SIZE = 10

    def __init__(self, widget):
        super().__init__()

        self.setWidget(widget)

        self.setPos(100, 100)

        self.setFlag(QGraphicsProxyWidget.ItemIsMovable, True)
        self.setFlag(QGraphicsProxyWidget.ItemIsSelectable, True)
        self.setFlag(QGraphicsProxyWidget.ItemSendsGeometryChanges, True)

        self.resizing = False
        self.resize_start_pos = QPointF()
        self.start_rect = QRectF()

        self.on_select_callback = None

        self.setZValue(1)

    def boundingRect(self):
        return self.widget().rect()

    # ---------------- SELECTION ----------------
    def mousePressEvent(self, event):

        if self.is_on_corner(event.pos()):
            self.resizing = True
            self.resize_start_pos = event.pos()
            self.start_rect = self.widget().rect()
            event.accept()
            return

        super().mousePressEvent(event)

        if self.on_select_callback:
            self.on_select_callback(self)

    # ---------------- RESIZE ----------------
    def mouseMoveEvent(self, event):

        if self.resizing:

            delta = event.pos() - self.resize_start_pos

            new_width = max(100, self.start_rect.width() + delta.x())
            new_height = max(80, self.start_rect.height() + delta.y())

            self.widget().resize(new_width, new_height)

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):

        self.resizing = False
        super().mouseReleaseEvent(event)

    # ---------------- HELPERS ----------------
    def is_on_corner(self, pos):

        rect = self.widget().rect()

        return (
            rect.width() - self.HANDLE_SIZE <= pos.x() <= rect.width()
            and rect.height() - self.HANDLE_SIZE <= pos.y() <= rect.height()
        )

    # ---------------- PROPERTIES ----------------
    def get_properties(self):

        rect = self.widget().rect()

        return {
            "x": int(self.x()),
            "y": int(self.y()),
            "width": int(rect.width()),
            "height": int(rect.height()),
        }