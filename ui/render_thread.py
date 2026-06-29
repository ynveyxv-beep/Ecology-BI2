from PySide6.QtCore import QThread, Signal
import plotly.graph_objects as go
import plotly.io as pio
from PySide6.QtGui import QPixmap


class RenderThread(QThread):
    """Поток для рендеринга графиков Plotly"""
    
    finished = Signal(object)  # Сигнал с QPixmap
    error = Signal(str)
    
    def __init__(self, fig, width, height, scale=1.2):
        super().__init__()
        self.fig = fig
        self.width = width
        self.height = height
        self.scale = scale
        self._is_running = True
    
    def run(self):
        """Запуск рендеринга в потоке"""
        try:
            # Генерируем изображение
            img_bytes = pio.to_image(
                self.fig,
                format="png",
                width=self.width,
                height=self.height,
                scale=self.scale
            )
            
            if not self._is_running:
                return
            
            # Создаём QPixmap из данных
            pix = QPixmap()
            if pix.loadFromData(img_bytes):
                self.finished.emit(pix)
            else:
                self.error.emit("Failed to load image")
                
        except Exception as e:
            self.error.emit(str(e))
    
    def stop(self):
        """Остановка потока"""
        self._is_running = False