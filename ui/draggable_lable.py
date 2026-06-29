from PySide6.QtCore import Qt
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QLabel


class DraggableLabel(QLabel):

    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("""
            QLabel {
                padding: 6px;
                background: #eaeaea;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(28)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.startDrag()

    def startDrag(self):

        drag = QDrag(self)

        mime = self.text()

        from PySide6.QtCore import QMimeData
        data = QMimeData()
        data.setText(mime)

        drag.setMimeData(data)
        drag.exec()