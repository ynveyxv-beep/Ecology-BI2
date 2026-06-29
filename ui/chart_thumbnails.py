import pyqtgraph as pg
import numpy as np
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtCore import Qt


class ChartThumbnailGenerator:
    """Генератор миниатюр для кнопок графиков"""
    
    @staticmethod
    def generate_thumbnail(chart_type, width=140, height=60):
        """Генерирует миниатюру для указанного типа графика"""
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(240, 240, 240))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Генерируем данные в зависимости от типа
        if chart_type == "line":
            ChartThumbnailGenerator._draw_line(painter, width, height)
        elif chart_type == "scatter":
            ChartThumbnailGenerator._draw_scatter(painter, width, height)
        elif chart_type == "bar":
            ChartThumbnailGenerator._draw_bar(painter, width, height)
        elif chart_type == "area":
            ChartThumbnailGenerator._draw_area(painter, width, height)
        elif chart_type == "pie":
            ChartThumbnailGenerator._draw_pie(painter, width, height)
        elif chart_type == "donut":
            ChartThumbnailGenerator._draw_donut(painter, width, height)
        elif chart_type == "histogram":
            ChartThumbnailGenerator._draw_histogram(painter, width, height)
        elif chart_type == "boxplot":
            ChartThumbnailGenerator._draw_boxplot(painter, width, height)
        elif chart_type == "heatmap":
            ChartThumbnailGenerator._draw_heatmap(painter, width, height)
        elif chart_type == "map":
            ChartThumbnailGenerator._draw_map(painter, width, height)
        elif chart_type == "treemap":
            ChartThumbnailGenerator._draw_treemap(painter, width, height)
        elif chart_type == "funnel":
            ChartThumbnailGenerator._draw_funnel(painter, width, height)
        elif chart_type == "gauge":
            ChartThumbnailGenerator._draw_gauge(painter, width, height)
        elif chart_type == "waterfall":
            ChartThumbnailGenerator._draw_waterfall(painter, width, height)
        else:
            ChartThumbnailGenerator._draw_line(painter, width, height)
        
        painter.end()
        return pixmap
    
    # =========================================================
    # ОТДЕЛЬНЫЕ МЕТОДЫ ДЛЯ КАЖДОГО ТИПА
    # =========================================================
    
    @staticmethod
    def _draw_line(painter, width, height):
        """Линейный график"""
        np.random.seed(42)
        x = np.linspace(0, width, 30)
        y = 10 + 30 * np.sin(x / 10) + np.random.normal(0, 3, 30)
        y = np.clip(y, 5, height - 5)
        
        # Создаём QColor
        color = QColor(0, 120, 215)
        
        # Рисуем линию
        painter.setPen(pg.mkPen(color, width=2))
        
        # Рисуем точки
        for i in range(len(x) - 1):
            painter.drawLine(int(x[i]), int(y[i]), int(x[i+1]), int(y[i+1]))
    
    @staticmethod
    def _draw_scatter(painter, width, height):
        """Точечный график"""
        np.random.seed(42)
        x = np.random.uniform(10, width - 10, 20)
        y = np.random.uniform(10, height - 10, 20)
        
        color = QColor(0, 120, 215, 180)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        
        for i in range(len(x)):
            painter.drawEllipse(int(x[i]) - 3, int(y[i]) - 3, 6, 6)
    
    @staticmethod
    def _draw_bar(painter, width, height):
        """Столбчатый график"""
        np.random.seed(42)
        n_bars = 8
        x = np.arange(n_bars) * (width / n_bars) + (width / n_bars / 2)
        values = np.random.uniform(10, height - 10, n_bars)
        
        bar_width = (width / n_bars) * 0.6
        color = QColor(0, 120, 215)
        
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        
        for i in range(n_bars):
            x_pos = x[i] - bar_width / 2
            y_pos = height - values[i]
            painter.drawRect(int(x_pos), int(y_pos), int(bar_width), int(values[i]))
    
    @staticmethod
    def _draw_area(painter, width, height):
        """График с заливкой"""
        np.random.seed(42)
        x = np.linspace(0, width, 30)
        y = 10 + 30 * np.sin(x / 10) + np.random.normal(0, 2, 30)
        y = np.clip(y, 5, height - 5)
        
        # Заливка
        fill_color = QColor(0, 120, 215, 100)
        line_color = QColor(0, 120, 215)
        
        # Рисуем заливку
        painter.setBrush(fill_color)
        painter.setPen(Qt.NoPen)
        
        points = []
        for i in range(len(x)):
            points.append((int(x[i]), int(y[i])))
        points.append((int(x[-1]), height))
        points.append((int(x[0]), height))
        
        # Рисуем полигон
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
        
        # Линия сверху
        painter.setPen(pg.mkPen(line_color, width=2))
        for i in range(len(x) - 1):
            painter.drawLine(int(x[i]), int(y[i]), int(x[i+1]), int(y[i+1]))
    
    @staticmethod
    def _draw_pie(painter, width, height):
        """Круговая диаграмма"""
        center_x = width // 2
        center_y = height // 2
        radius = min(width, height) // 2 - 5
        
        colors = [
            QColor(0, 120, 215), QColor(212, 56, 13), QColor(212, 160, 13),
            QColor(13, 140, 74), QColor(140, 13, 180), QColor(13, 140, 180)
        ]
        
        values = [30, 25, 20, 15, 10]
        total = sum(values)
        start_angle = -90 * 16  # В 16 раз больше для drawPie
        
        for i, val in enumerate(values):
            angle = (val / total) * 360 * 16
            color = colors[i % len(colors)]
            painter.setBrush(color)
            painter.setPen(QColor(255, 255, 255))
            painter.drawPie(
                center_x - radius, center_y - radius,
                radius * 2, radius * 2,
                int(start_angle), int(angle)
            )
            start_angle += angle
    
    @staticmethod
    def _draw_donut(painter, width, height):
        """Кольцевая диаграмма"""
        center_x = width // 2
        center_y = height // 2
        radius = min(width, height) // 2 - 5
        
        colors = [
            QColor(0, 120, 215), QColor(212, 56, 13), QColor(212, 160, 13),
            QColor(13, 140, 74), QColor(140, 13, 180)
        ]
        
        values = [30, 25, 20, 15, 10]
        total = sum(values)
        start_angle = -90 * 16
        
        for i, val in enumerate(values):
            angle = (val / total) * 360 * 16
            color = colors[i % len(colors)]
            painter.setBrush(color)
            painter.setPen(QColor(255, 255, 255))
            painter.drawPie(
                center_x - radius, center_y - radius,
                radius * 2, radius * 2,
                int(start_angle), int(angle)
            )
            start_angle += angle
        
        # Внутренний круг (дырка)
        inner_radius = radius * 0.4
        painter.setBrush(QColor(240, 240, 240))
        painter.setPen(QColor(255, 255, 255))
        painter.drawEllipse(
            center_x - inner_radius, center_y - inner_radius,
            inner_radius * 2, inner_radius * 2
        )
    
    @staticmethod
    def _draw_histogram(painter, width, height):
        """Гистограмма"""
        np.random.seed(42)
        data = np.random.normal(height // 2, height // 4, 1000)
        hist, bins = np.histogram(data, bins=10)
        hist = hist / max(hist) * (height - 10)
        
        bin_width = width / len(hist)
        color = QColor(0, 120, 215)
        
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        
        for i in range(len(hist)):
            x = i * bin_width + 2
            h = hist[i]
            painter.drawRect(int(x), int(height - h), int(bin_width - 4), int(h))
    
    @staticmethod
    def _draw_boxplot(painter, width, height):
        """Ящик с усами"""
        np.random.seed(42)
        data = np.random.normal(height // 2, height // 4, 100)
        
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        median = np.median(data)
        iqr = q3 - q1
        lower = max(np.min(data), q1 - 1.5 * iqr)
        upper = min(np.max(data), q3 + 1.5 * iqr)
        
        center_x = width // 2
        box_width = 20
        
        # Ящик
        painter.setBrush(QColor(0, 120, 215))
        painter.setPen(QColor(0, 0, 0))
        painter.drawRect(
            center_x - box_width // 2,
            int(height - q3),
            box_width,
            int(q3 - q1)
        )
        
        # Медиана
        painter.setPen(QColor(255, 0, 0))
        painter.drawLine(
            center_x - box_width // 2,
            int(height - median),
            center_x + box_width // 2,
            int(height - median)
        )
        
        # Усы
        painter.setPen(QColor(0, 0, 0))
        painter.drawLine(center_x, int(height - upper), center_x, int(height - lower))
        painter.drawLine(center_x - 5, int(height - upper), center_x + 5, int(height - upper))
        painter.drawLine(center_x - 5, int(height - lower), center_x + 5, int(height - lower))
    
    @staticmethod
    def _draw_heatmap(painter, width, height):
        """Тепловая карта"""
        np.random.seed(42)
        data = np.random.rand(6, 8)
        
        cell_width = width / 8
        cell_height = height / 6
        
        for i in range(6):
            for j in range(8):
                val = data[i][j]
                color_val = int(255 * val)
                painter.fillRect(
                    int(j * cell_width),
                    int(i * cell_height),
                    int(cell_width),
                    int(cell_height),
                    QColor(0, 0, color_val)
                )
    
    @staticmethod
    def _draw_map(painter, width, height):
        """Карта"""
        # Зелёный фон
        painter.fillRect(0, 0, width, height, QColor(200, 230, 200))
        
        # Силуэт континента
        points = [
            (width * 0.2, height * 0.4),
            (width * 0.3, height * 0.2),
            (width * 0.5, height * 0.15),
            (width * 0.7, height * 0.25),
            (width * 0.8, height * 0.4),
            (width * 0.7, height * 0.6),
            (width * 0.5, height * 0.7),
            (width * 0.3, height * 0.6),
        ]
        
        painter.setBrush(QColor(100, 180, 100))
        painter.setPen(QColor(0, 100, 0))
        
        # Рисуем полигон
        for i in range(len(points) - 1):
            painter.drawLine(int(points[i][0]), int(points[i][1]), 
                           int(points[i+1][0]), int(points[i+1][1]))
        
        # Маркеры
        np.random.seed(42)
        for _ in range(3):
            x = np.random.uniform(width * 0.25, width * 0.75)
            y = np.random.uniform(height * 0.25, height * 0.75)
            painter.setBrush(QColor(255, 0, 0, 150))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(x) - 3, int(y) - 3, 6, 6)
    
    @staticmethod
    def _draw_treemap(painter, width, height):
        """Древовидная карта"""
        colors = [
            QColor(0, 120, 215), QColor(212, 56, 13), QColor(212, 160, 13),
            QColor(13, 140, 74), QColor(140, 13, 180), QColor(13, 140, 180)
        ]
        
        rects = [
            (0, 0, width * 0.5, height * 0.5),
            (width * 0.5, 0, width * 0.3, height * 0.5),
            (width * 0.8, 0, width * 0.2, height * 0.5),
            (0, height * 0.5, width * 0.6, height * 0.3),
            (width * 0.6, height * 0.5, width * 0.4, height * 0.3),
            (0, height * 0.8, width * 1, height * 0.2),
        ]
        
        for i, rect in enumerate(rects):
            x, y, w, h = rect
            color = colors[i % len(colors)]
            painter.fillRect(int(x), int(y), int(w), int(h), color)
            painter.setPen(QColor(255, 255, 255))
            painter.drawRect(int(x), int(y), int(w), int(h))
    
    @staticmethod
    def _draw_funnel(painter, width, height):
        """Воронка"""
        levels = 5
        level_height = height / levels
        max_width = width * 0.8
        
        for i in range(levels):
            w = max_width * (1 - i * 0.15)
            x = (width - w) / 2
            y = i * level_height
            color_val = 200 - i * 30
            painter.fillRect(
                int(x), int(y),
                int(w), int(level_height - 2),
                QColor(color_val, 100, 100)
            )
            painter.setPen(QColor(255, 255, 255))
            painter.drawRect(
                int(x), int(y),
                int(w), int(level_height - 2)
            )
    
    @staticmethod
    def _draw_gauge(painter, width, height):
        """Спидометр"""
        center_x = width // 2
        center_y = height // 2
        radius = min(width, height) // 2 - 5
        
        # Дуга
        start_angle = -150 * 16
        span_angle = 300 * 16
        
        painter.setPen(QColor(200, 200, 200))
        painter.drawArc(
            center_x - radius, center_y - radius,
            radius * 2, radius * 2,
            start_angle, span_angle
        )
        
        # Зелёная часть
        painter.setPen(QColor(0, 200, 0))
        painter.drawArc(
            center_x - radius, center_y - radius,
            radius * 2, radius * 2,
            start_angle, 180 * 16
        )
        
        # Жёлтая часть
        painter.setPen(QColor(200, 200, 0))
        painter.drawArc(
            center_x - radius, center_y - radius,
            radius * 2, radius * 2,
            (start_angle + 180 * 16), 60 * 16
        )
        
        # Красная часть
        painter.setPen(QColor(200, 0, 0))
        painter.drawArc(
            center_x - radius, center_y - radius,
            radius * 2, radius * 2,
            (start_angle + 240 * 16), 60 * 16
        )
        
        # Стрелка
        angle = np.radians(-150 + 150)
        end_x = center_x + radius * 0.7 * np.cos(angle)
        end_y = center_y + radius * 0.7 * np.sin(angle)
        painter.setPen(QColor(0, 0, 0))
        painter.drawLine(center_x, center_y, int(end_x), int(end_y))
        
        # Центр
        painter.setBrush(QColor(0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center_x - 3, center_y - 3, 6, 6)
    
    @staticmethod
    def _draw_waterfall(painter, width, height):
        """Водопад"""
        np.random.seed(42)
        values = np.random.uniform(10, height - 10, 8)
        
        bar_width = width / len(values) * 0.6
        start_x = (width - len(values) * bar_width) / 2
        
        cumulative = height
        for i, val in enumerate(values):
            x = start_x + i * bar_width
            color = QColor(0, 120, 215) if i < 4 else QColor(212, 56, 13)
            painter.fillRect(
                int(x),
                int(cumulative - val),
                int(bar_width),
                int(val),
                color
            )
            painter.setPen(QColor(255, 255, 255))
            painter.drawRect(
                int(x),
                int(cumulative - val),
                int(bar_width),
                int(val)
            )
            cumulative -= val * 0.3