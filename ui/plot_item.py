import pyqtgraph as pg
import numpy as np
import pandas as pd
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer, QPoint
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QCursor
from PySide6.QtWidgets import QGraphicsProxyWidget, QGraphicsView, QWidget, QMenu, QColorDialog


class PlotItem(QGraphicsProxyWidget):
    """График на основе PyQtGraph для работы с большими данными"""
    
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
        chart_type,
        x_column,
        y_column=None,
        y_columns=None,
        aggregation="none",
        title="",
        color="#0078d4",
        show_legend=True,
        width=600,
        height=350,
    ):
        super().__init__()
        
        # Настройки для QGraphicsScene
        self.setFlag(QGraphicsProxyWidget.ItemIsMovable, True)
        self.setFlag(QGraphicsProxyWidget.ItemIsSelectable, True)
        self.setFlag(QGraphicsProxyWidget.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsProxyWidget.ItemIsFocusable, True)
        
        self.setAcceptHoverEvents(True)
        self.setAcceptTouchEvents(True)
        self.setFlag(QGraphicsProxyWidget.ItemStacksBehindParent, False)
        
        # Сохраняем данные
        self.df = dataframe
        self.chart_type = chart_type
        self.x_column = x_column
        
        # Поддержка множественных Y
        if y_columns:
            self.y_columns = y_columns
        elif y_column:
            self.y_columns = [y_column]
        else:
            self.y_columns = []
        
        self.aggregation = aggregation
        self.title = title
        self.color = color
        self.show_legend = show_legend
        
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
        
        # Флаг для предотвращения повторных вызовов
        self._is_building = False
        
        # Флаг для перемещения
        self._is_dragging = False
        self._drag_start_pos = None
        self._drag_start_item_pos = None
        
        # Хранилище для категорий (для pie)
        self._x_labels = {}
        
        try:
            # Создаём виджет PyQtGraph
            self.plot_widget = pg.PlotWidget()
            self.plot_widget.setBackground('white')
            
            # ОТКЛЮЧАЕМ события мыши у внутреннего виджета
            self.plot_widget.setMouseTracking(False)
            self.plot_widget.setAcceptDrops(False)
            
            # НАСТРОЙКИ ПРОИЗВОДИТЕЛЬНОСТИ
            try:
                self.plot_widget.setViewportUpdateMode(
                    QGraphicsView.MinimalViewportUpdate
                )
            except AttributeError:
                try:
                    self.plot_widget.setViewportUpdateMode(2)
                except:
                    pass
            
            # Устанавливаем виджет в QGraphicsProxyWidget
            self.setWidget(self.plot_widget)
            self.resize(width, height)
            
            # Контекстное меню
            self.plot_widget.setContextMenuPolicy(Qt.CustomContextMenu)
            self.plot_widget.customContextMenuRequested.connect(self.show_context_menu)
            
            # Строим график
            self.build_chart()
            
        except Exception as e:
            print(f"❌ Init error: {e}")
            self._create_fallback_widget()

    # =========================================================
    # FALLBACK
    # =========================================================
    
    def _create_fallback_widget(self):
        """Создаёт заглушку при ошибке"""
        try:
            fallback = QWidget()
            fallback.setStyleSheet("background: #fff5f5; color: #c0392b; padding: 20px;")
            fallback.setMouseTracking(False)
            self.setWidget(fallback)
        except:
            pass

    # =========================================================
    # DATA PREPARATION WITH AGGREGATION
    # =========================================================
    
    def _prepare_data(self, x_data, y_data):
        """Подготавливает данные для отображения с проверкой типов"""
        try:
            x = pd.Series(x_data) if not isinstance(x_data, pd.Series) else x_data
            y = pd.Series(y_data) if not isinstance(y_data, pd.Series) else y_data
            
            x_is_numeric = pd.api.types.is_numeric_dtype(x)
            y_is_numeric = pd.api.types.is_numeric_dtype(y)
            
            if not x_is_numeric or not y_is_numeric:
                print(f"⚠️ Non-numeric data detected. Converting to indices...")
                if not x_is_numeric:
                    unique_x = x.unique()
                    x_map = {val: i for i, val in enumerate(unique_x)}
                    x = pd.Series([x_map[val] for val in x])
                    self._x_labels = {i: str(val) for i, val in enumerate(unique_x)}
                
                if not y_is_numeric:
                    try:
                        y = pd.to_numeric(y, errors='coerce')
                    except:
                        y = pd.Series(range(len(y)))
            
            if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
                mask = pd.Series([True] * len(x))
                mask &= x.notna() & np.isfinite(x)
                mask &= y.notna() & np.isfinite(y)
                x = x[mask]
                y = y[mask]
            else:
                mask = x.notna() & y.notna()
                x = x[mask]
                y = y[mask]
            
            x_arr = np.array(x)
            y_arr = np.array(y)
            
            return x_arr, y_arr
            
        except Exception as e:
            print(f"❌ Data preparation error: {e}")
            return np.arange(len(x_data)), np.arange(len(y_data))

    def _apply_aggregation(self, df, x_col, y_col):
        """Применяет агрегацию к данным используя pandas"""
        try:
            if x_col not in df.columns or y_col not in df.columns:
                return self._prepare_data(df[x_col].values, df[y_col].values)
            
            # Для круговой диаграммы своя логика
            if self.chart_type == "pie":
                return self._prepare_pie_data(df, x_col, y_col)
            
            if self.aggregation == "none":
                return self._prepare_data(df[x_col].values, df[y_col].values)
            
            if not pd.api.types.is_numeric_dtype(df[y_col]):
                print(f"⚠️ Column '{y_col}' is not numeric, skipping aggregation")
                return self._prepare_data(df[x_col].values, df[y_col].values)
            
            grouped = df.groupby(x_col)[y_col]
            
            if self.aggregation == "SUM":
                result = grouped.sum()
            elif self.aggregation == "AVG":
                result = grouped.mean()
            elif self.aggregation == "COUNT":
                result = grouped.count()
            elif self.aggregation == "MIN":
                result = grouped.min()
            elif self.aggregation == "MAX":
                result = grouped.max()
            elif self.aggregation == "MEDIAN":
                result = grouped.median()
            else:
                return self._prepare_data(df[x_col].values, df[y_col].values)
            
            x_agg = result.index.values
            y_agg = result.values
            
            print(f"✅ Aggregation '{self.aggregation}' applied: {len(x_agg)} groups")
            return self._prepare_data(x_agg, y_agg)
            
        except Exception as e:
            print(f"❌ Aggregation error: {e}")
            return self._prepare_data(df[x_col].values, df[y_col].values)

    def _prepare_pie_data(self, df, x_col, y_col):
        """Подготавливает данные для круговой диаграммы"""
        try:
            # Группируем по X и суммируем Y
            grouped = df.groupby(x_col)[y_col].sum()
            
            # Сортируем по убыванию
            grouped = grouped.sort_values(ascending=False)
            
            # Ограничиваем количество сегментов (топ-10)
            if len(grouped) > 10:
                top = grouped.head(10)
                other_sum = grouped[10:].sum()
                # Добавляем "Other" если есть
                if other_sum > 0:
                    top = pd.concat([top, pd.Series([other_sum], index=['Other'])])
                grouped = top
            
            labels = grouped.index.values
            values = grouped.values
            
            return labels, values
            
        except Exception as e:
            print(f"❌ Pie data preparation error: {e}")
            return df[x_col].values[:10], df[y_col].values[:10]

    # =========================================================
    # BUILD CHART
    # =========================================================
    
    def build_chart(self):
        """Строит график в зависимости от типа"""
        if self._is_building:
            return
        
        self._is_building = True
        
        try:
            if self.df is None or self.df.empty:
                self._show_message("No data available", (200, 150, 0))
                return
            
            if self.x_column not in self.df.columns:
                self._show_message(f"Column '{self.x_column}' not found", (200, 0, 0))
                return
            
            self.plot_widget.clear()
            
            if not self.y_columns:
                self._show_message("No Y columns selected", (200, 150, 0))
                return
            
            valid_y_columns = [col for col in self.y_columns if col in self.df.columns]
            if not valid_y_columns:
                self._show_message("No valid Y columns", (200, 0, 0))
                return
            
            # Для разных типов графиков своя логика
            if self.chart_type == "pie":
                self._build_pie(valid_y_columns[0])
            elif self.chart_type == "area":
                self._build_area(valid_y_columns)
            elif self.chart_type == "heatmap":
                self._build_heatmap(valid_y_columns)
            else:
                self._build_standard_chart(valid_y_columns)
            
            # Добавляем обработчик кликов
            self._add_click_handler()
            
        except Exception as e:
            print(f"❌ Build chart error: {e}")
            import traceback
            traceback.print_exc()
            self._show_message(f"Error: {str(e)}", (200, 0, 0))
        finally:
            self._is_building = False

    # =========================================================
    # STANDARD CHART (line, scatter, bar, histogram, boxplot)
    # =========================================================
    
    def _build_standard_chart(self, valid_y_columns):
        """Строит стандартные графики (line, scatter, bar, histogram, boxplot)"""
        colors = [
            "#0078d4", "#d4380d", "#d4a00d", "#0d8c4a", 
            "#8c0db4", "#0d8cb4", "#b40d8c", "#8c8c0d"
        ]
        
        for i, y_col in enumerate(valid_y_columns):
            x_plot, y_plot = self._apply_aggregation(self.df, self.x_column, y_col)
            
            if len(x_plot) == 0:
                continue
            
            if len(x_plot) > 10000:
                step = max(1, len(x_plot) // 10000)
                x_plot = x_plot[::step]
                y_plot = y_plot[::step]
            
            color = colors[i % len(colors)]
            
            if self.chart_type == "line":
                pen = pg.mkPen(color=color, width=1.5)
                self.plot_widget.plot(x_plot, y_plot, pen=pen, name=y_col)
                
            elif self.chart_type == "scatter":
                scatter = pg.ScatterPlotItem(
                    x=x_plot,
                    y=y_plot,
                    size=5,
                    brush=pg.mkBrush(color),
                    pen=pg.mkPen(None)
                )
                self.plot_widget.addItem(scatter)
                
            elif self.chart_type == "bar":
                if i == 0:
                    if len(x_plot) > 100:
                        x_plot = x_plot[:100]
                        y_plot = y_plot[:100]
                    
                    bg = pg.BarGraphItem(
                        x=np.arange(len(x_plot)),
                        height=y_plot,
                        width=0.6,
                        brush=pg.mkBrush(color)
                    )
                    self.plot_widget.addItem(bg)
                    
                    x_ticks = [(i, str(x_plot[i])) for i in range(min(len(x_plot), 20))]
                    if x_ticks:
                        try:
                            ax = self.plot_widget.getAxis('bottom')
                            ax.setTicks([x_ticks])
                        except:
                            pass
            
            elif self.chart_type == "histogram":
                if i == 0:
                    self._build_histogram(x_plot)
            
            elif self.chart_type == "boxplot":
                if i == 0:
                    self._build_boxplot(y_plot)
        
        self._add_chart_elements(valid_y_columns)

    # =========================================================
    # AREA CHART
    # =========================================================
    
    def _build_area(self, valid_y_columns):
        """Строит график с заливкой (Area)"""
        colors = [
            "#0078d4", "#d4380d", "#d4a00d", "#0d8c4a", 
            "#8c0db4", "#0d8cb4", "#b40d8c", "#8c8c0d"
        ]
        
        for i, y_col in enumerate(valid_y_columns):
            x_plot, y_plot = self._apply_aggregation(self.df, self.x_column, y_col)
            
            if len(x_plot) == 0:
                continue
            
            if len(x_plot) > 10000:
                step = max(1, len(x_plot) // 10000)
                x_plot = x_plot[::step]
                y_plot = y_plot[::step]
            
            color = colors[i % len(colors)]
            
            # Линия
            pen = pg.mkPen(color=color, width=1.5)
            curve = self.plot_widget.plot(x_plot, y_plot, pen=pen, name=y_col)
            
            # Заливка под линией
            fill_brush = pg.mkBrush(color=color, alpha=80)
            
            # Создаём заполненную область с помощью FillBetweenItem
            # Используем простой подход - добавляем вторую линию на нуле
            zero_line = pg.PlotDataItem(x_plot, np.zeros_like(y_plot), pen=None)
            self.plot_widget.addItem(zero_line)
            
            try:
                fill = pg.FillBetweenItem(curve, zero_line, brush=fill_brush)
                self.plot_widget.addItem(fill)
            except:
                # Если FillBetweenItem не работает, рисуем заливку вручную
                self._draw_area_fill(x_plot, y_plot, color)
        
        self._add_chart_elements(valid_y_columns)

    def _draw_area_fill(self, x, y, color):
        """Рисует заливку под линией вручную"""
        try:
            # Создаём полигон из точек
            points = []
            for i in range(len(x)):
                points.append((x[i], y[i]))
            # Добавляем точки на нулевой линии в обратном порядке
            for i in range(len(x)-1, -1, -1):
                points.append((x[i], 0))
            
            # Создаём полигон
            polygon = pg.PolygonROI(
                points, 
                pen=None,
                brush=pg.mkBrush(color=color, alpha=80)
            )
            self.plot_widget.addItem(polygon)
        except:
            pass

    # =========================================================
    # PIE CHART
    # =========================================================
    
    def _build_pie(self, y_col):
        """Строит круговую диаграмму"""
        labels, values = self._apply_aggregation(self.df, self.x_column, y_col)
        
        if len(labels) == 0:
            self._show_message("No data for pie chart", (200, 150, 0))
            return
        
        # Цветовая палитра для сегментов
        colors = [
            "#0078d4", "#d4380d", "#d4a00d", "#0d8c4a", 
            "#8c0db4", "#0d8cb4", "#b40d8c", "#8c8c0d",
            "#d4388c", "#0d8c8c", "#8c8c0d", "#8c0d8c"
        ]
        
        # Очищаем график
        self.plot_widget.clear()
        
        # Рисуем сегменты круга
        total = sum(values)
        start_angle = 0
        
        for i, (label, value) in enumerate(zip(labels, values)):
            if value == 0 or total == 0:
                continue
            
            angle = (value / total) * 360
            color = colors[i % len(colors)]
            
            # Рисуем сектор с помощью BarGraphItem (круговая диаграмма через столбцы)
            # Или используем текст для отображения
            x_pos = np.cos(np.radians(start_angle + angle/2)) * 100
            y_pos = np.sin(np.radians(start_angle + angle/2)) * 100
            
            # Добавляем текстовую метку
            text = f"{label}\n{value:.1f}%"
            text_item = pg.TextItem(
                text,
                color=pg.mkColor(color),
                anchor=(0.5, 0.5)
            )
            text_item.setPos(x_pos, y_pos)
            self.plot_widget.addItem(text_item)
            
            start_angle += angle
        
        # Добавляем круглую рамку
        circle = pg.CircleROI(
            pos=(-100, -100),
            size=(200, 200),
            pen=pg.mkPen(color='black', width=1),
            brush=None
        )
        self.plot_widget.addItem(circle)
        
        # Настраиваем оси для круговой диаграммы
        self.plot_widget.setAspectLocked(True)
        self.plot_widget.setXRange(-120, 120)
        self.plot_widget.setYRange(-120, 120)
        self.plot_widget.getAxis('bottom').setTicks([[]])
        self.plot_widget.getAxis('left').setTicks([[]])
        
        if self.title:
            try:
                self.plot_widget.setTitle(self.title)
            except:
                pass

    # =========================================================
    # HEATMAP
    # =========================================================
    
    def _build_heatmap(self, valid_y_columns):
        """Строит тепловую карту (Heatmap)"""
        if len(valid_y_columns) < 2:
            self._show_message("Heatmap requires at least 2 Y columns", (200, 150, 0))
            return
        
        try:
            # Берем первые две Y-колонки для тепловой карты
            y1 = valid_y_columns[0]
            y2 = valid_y_columns[1] if len(valid_y_columns) > 1 else valid_y_columns[0]
            
            # Получаем данные
            x_plot, y1_plot = self._apply_aggregation(self.df, self.x_column, y1)
            _, y2_plot = self._apply_aggregation(self.df, self.x_column, y2)
            
            if len(x_plot) == 0 or len(y1_plot) == 0 or len(y2_plot) == 0:
                self._show_message("No data for heatmap", (200, 150, 0))
                return
            
            # Создаём матрицу для тепловой карты
            # Используем простой подход - ScatterPlotItem с цветами
            # Нормализуем значения для цветов
            y1_norm = (y1_plot - np.min(y1_plot)) / (np.max(y1_plot) - np.min(y1_plot) + 0.001)
            y2_norm = (y2_plot - np.min(y2_plot)) / (np.max(y2_plot) - np.min(y2_plot) + 0.001)
            
            # Создаём точки с цветами на основе второй переменной
            colors = []
            for val in y2_norm:
                # От синего к красному
                r = int(255 * val)
                g = int(255 * (1 - abs(val - 0.5) * 2) * 0.5)
                b = int(255 * (1 - val))
                colors.append((r, g, b, 180))
            
            scatter = pg.ScatterPlotItem(
                x=x_plot,
                y=y1_plot,
                size=15,
                brush=[pg.mkBrush(*c) for c in colors],
                pen=pg.mkPen(None)
            )
            self.plot_widget.addItem(scatter)
            
            # Подписи
            self.plot_widget.setLabel('bottom', self.x_column)
            self.plot_widget.setLabel('left', y1)
            
            # Добавляем цветовую шкалу
            # Простая легенда
            legend_text = f"Color: {y2}"
            text_item = pg.TextItem(
                legend_text,
                color=pg.mkColor(50, 50, 50),
                anchor=(0, 0)
            )
            text_item.setPos(0, 0)
            self.plot_widget.addItem(text_item)
            
            self._add_chart_elements([y1, y2])
            
        except Exception as e:
            print(f"❌ Heatmap error: {e}")
            self._show_message(f"Heatmap error: {str(e)}", (200, 0, 0))

    # =========================================================
    # HISTOGRAM & BOXPLOT
    # =========================================================
    
    def _build_histogram(self, x_data):
        try:
            if not pd.api.types.is_numeric_dtype(x_data):
                self._show_message("Histogram requires numeric data", (200, 150, 0))
                return
            
            hist, bins = np.histogram(x_data, bins=50)
            x = (bins[:-1] + bins[1:]) / 2
            
            bg = pg.BarGraphItem(
                x=x,
                height=hist,
                width=(bins[1] - bins[0]) * 0.8,
                brush=pg.mkBrush(self.color)
            )
            self.plot_widget.addItem(bg)
            self.plot_widget.setLabel('left', 'Frequency')
        except Exception as e:
            print(f"❌ Histogram error: {e}")
    
    def _build_boxplot(self, y_data):
        try:
            if not pd.api.types.is_numeric_dtype(y_data):
                self._show_message("BoxPlot requires numeric data", (200, 150, 0))
                return
            
            q1 = np.percentile(y_data, 25)
            q3 = np.percentile(y_data, 75)
            median = np.median(y_data)
            iqr = q3 - q1
            lower_whisker = max(np.min(y_data), q1 - 1.5 * iqr)
            upper_whisker = min(np.max(y_data), q3 + 1.5 * iqr)
            
            box = pg.BarGraphItem(
                x=[0],
                height=[q3 - q1],
                width=[0.6],
                brush=pg.mkBrush(self.color)
            )
            box.setPos(0, q1)
            self.plot_widget.addItem(box)
            
            median_line = pg.InfiniteLine(
                pos=median,
                angle=0,
                pen=pg.mkPen(color='red', width=2)
            )
            self.plot_widget.addItem(median_line)
            
            whisker_top = pg.InfiniteLine(
                pos=upper_whisker,
                angle=0,
                pen=pg.mkPen(color='black', width=1)
            )
            self.plot_widget.addItem(whisker_top)
            
            whisker_bottom = pg.InfiniteLine(
                pos=lower_whisker,
                angle=0,
                pen=pg.mkPen(color='black', width=1)
            )
            self.plot_widget.addItem(whisker_bottom)
            
            outliers = y_data[(y_data < lower_whisker) | (y_data > upper_whisker)]
            if len(outliers) > 0:
                scatter = pg.ScatterPlotItem(
                    x=np.zeros(len(outliers)),
                    y=outliers,
                    size=5,
                    brush=pg.mkBrush(200, 0, 0, 150),
                    pen=pg.mkPen(None)
                )
                self.plot_widget.addItem(scatter)
            
            self.plot_widget.setLabel('left', self.y_columns[0] if self.y_columns else 'Value')
            try:
                self.plot_widget.getAxis('bottom').setTicks([[]])
            except:
                pass
        except Exception as e:
            print(f"❌ Boxplot error: {e}")

    # =========================================================
    # CHART ELEMENTS (legend, title, grid, labels)
    # =========================================================
    
    def _add_chart_elements(self, valid_y_columns):
        """Добавляет легенду, заголовок, подписи осей и сетку"""
        if self.show_legend:
            try:
                self.plot_widget.addLegend()
            except:
                pass
        
        if self.title:
            try:
                self.plot_widget.setTitle(self.title)
            except:
                pass
        
        try:
            self.plot_widget.setLabel('bottom', self.x_column)
            if len(valid_y_columns) == 1:
                self.plot_widget.setLabel('left', valid_y_columns[0])
            else:
                self.plot_widget.setLabel('left', 'Value')
        except:
            pass
        
        try:
            plot_item = self.plot_widget.getPlotItem()
            try:
                plot_item.setDownsampling(auto=True, mode='peak')
            except:
                pass
            try:
                plot_item.setClipToView(True)
            except:
                pass
        except:
            pass
        
        try:
            self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        except:
            pass
    
    def _show_message(self, message, color=(100, 100, 100)):
        try:
            self.plot_widget.clear()
            text = pg.TextItem(message, color=pg.mkColor(color[0], color[1], color[2]))
            self.plot_widget.addItem(text)
        except:
            pass

    # =========================================================
    # CLICK HANDLER (для связанных графиков)
    # =========================================================
    
    def _add_click_handler(self):
        """Добавляет обработчик кликов по графику"""
        try:
            # Получаем PlotItem из pyqtgraph
            plot_item = self.plot_widget.getPlotItem()
            
            # Сохраняем ссылку на себя для использования в обработчике
            self._plot_item_ref = self
            
            # Создаём прокси-функцию для обработки кликов
            # Используем signal proxy для передачи кликов
            self.plot_widget.scene().sigMouseClicked.connect(
                lambda event: self._on_plot_click(event)
            )
        except Exception as e:
            print(f"⚠️ Click handler error: {e}")
    
    def _on_plot_click(self, event):
        """Обработчик клика по графику"""
        try:
            # Получаем координаты клика в системе координат графика
            pos = event.scenePos()
            
            # Получаем PlotItem
            plot_item = self.plot_widget.getPlotItem()
            
            # Получаем координаты в системе графика
            view_box = plot_item.getViewBox()
            if view_box is None:
                return
            
            # Преобразуем координаты
            mouse_point = view_box.mapSceneToView(pos)
            x_click = mouse_point.x()
            y_click = mouse_point.y()
            
            # Получаем данные графика
            x_data = self.df[self.x_column].values
            y_data = self.df[self.y_columns[0]].values if self.y_columns else []
            
            if len(x_data) == 0 or len(y_data) == 0:
                return
            
            # Находим ближайшую точку
            distances = np.sqrt((x_data - x_click) ** 2 + (y_data - y_click) ** 2)
            min_idx = np.argmin(distances)
            closest_x = x_data[min_idx]
            closest_y = y_data[min_idx]
            
            # Проверяем, что клик был близко к точке (порог 10% от диапазона)
            x_range = np.max(x_data) - np.min(x_data)
            y_range = np.max(y_data) - np.min(y_data)
            threshold = min(x_range, y_range) * 0.05  # 5% от диапазона
            
            if distances[min_idx] > threshold:
                return
            
            print(f"🖱️ Click detected: X={closest_x}, Y={closest_y}")
            
            # Отправляем сигнал в MainWindow через сцену
            if self.scene() and hasattr(self.scene().views()[0], 'parent'):
                main_window = self.scene().views()[0].parent()
                if main_window and hasattr(main_window, 'on_chart_clicked'):
                    main_window.on_chart_clicked(
                        self.x_column, 
                        closest_x,
                        self.y_columns[0] if self.y_columns else None,
                        closest_y
                    )
                    
        except Exception as e:
            print(f"❌ Click handler error: {e}")
            import traceback
            traceback.print_exc()

    # =========================================================
    # CONTEXT MENU
    # =========================================================
    
    def show_context_menu(self, pos):
        """Показывает контекстное меню для графика"""
        menu = QMenu()
        
        # Изменить цвет фона
        bg_action = menu.addAction("🎨 Change Background")
        bg_action.triggered.connect(self.change_background)
        
        menu.addSeparator()
        
        # Удалить
        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(self.delete_self)
        
        menu.exec(self.plot_widget.mapToGlobal(pos))
    
    def change_background(self):
        """Изменяет цвет фона графика"""
        try:
            current_color = self.plot_widget.getPlotItem().getViewBox().backgroundColor()
            color = QColorDialog.getColor(current_color, self.plot_widget, "Choose Background Color")
            if color.isValid():
                self.plot_widget.getPlotItem().getViewBox().setBackgroundColor(color.name())
                # Перерисовываем график
                self.build_chart()
        except Exception as e:
            print(f"❌ Change background error: {e}")
    
    def delete_self(self):
        """Удаляет график"""
        if self.scene():
            self.scene().removeItem(self)

    # =========================================================
    # UPDATE PROPERTIES
    # =========================================================
    
    def update_properties(self, properties: dict):
        if "y_columns" in properties and properties["y_columns"]:
            self.y_columns = properties["y_columns"]
        if "aggregation" in properties:
            self.aggregation = properties["aggregation"]
            print(f"🔄 Aggregation set to: {self.aggregation}")
        if "title" in properties:
            self.title = properties["title"]
        if "color" in properties:
            self.color = properties["color"]
        if "show_legend" in properties:
            self.show_legend = properties["show_legend"]
        if "width" in properties:
            self.chart_width = properties["width"]
        if "height" in properties:
            self.chart_height = properties["height"]
        
        self.build_chart()

    # =========================================================
    # RESIZE
    # =========================================================
    
    def resize(self, width, height):
        try:
            super().resize(width, height)
            if hasattr(self, 'plot_widget'):
                self.plot_widget.resize(width, height)
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
    # DELETE
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
            from pyqtgraph.exporters import ImageExporter
            exporter = ImageExporter(self.plot_widget.plotItem)
            exporter.parameters()['width'] = self.chart_width * scale
            exporter.parameters()['height'] = self.chart_height * scale
            exporter.export(path)
            print(f"✅ Exported to {path}")
        except Exception as e:
            print(f"❌ Export error: {e}")

    def get_properties(self):
        return {
            "type": "plot",
            "chart_type": self.chart_type,
            "x": int(self.x()),
            "y": int(self.y()),
            "width": self.chart_width,
            "height": self.chart_height,
            "x_column": self.x_column,
            "y_columns": self.y_columns,
            "aggregation": self.aggregation,
            "title": self.title,
            "color": self.color,
            "show_legend": self.show_legend
        }