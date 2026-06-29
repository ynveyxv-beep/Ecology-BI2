from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QMainWindow,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
    QTabWidget,
    QHBoxLayout,
    QMessageBox,
    QGraphicsTextItem,
    QDialog,
    QGraphicsProxyWidget,
    QInputDialog,
)
from PySide6.QtGui import QAction, QIcon
from typing import Dict, Any

import pandas as pd
import pyqtgraph as pg

from ui.grid_canvas import GridCanvas
from ui.plot_item import PlotItem
from ui.map_item import MapItem
from ui.text_item import TextItem
from ui.shape_item import ShapeItem
from ui.properties_panel import PropertiesPanel
from ui.filter_panel import FilterPanel
from ui.dashboard.page_tab_bar import PageTabBar
from ui.export_preview_dialog import ExportPreviewDialog
from ui.chart_thumbnails import ChartThumbnailGenerator
from core.project_io import ProjectIO
from core.data_manager import DataManager
from core.dashboard_model import DashboardManager, ChartConfig, Dashboard
from core.history_manager import HistoryManager
from core.template_manager import TemplateManager
from ui.dashboard.template_dialog import TemplateDialog
from ui.dashboard.tab_bar import TabBar


class ConfiguratorWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("BI Builder - Dashboard Editor")
        self.resize(1600, 900)

        # Инициализация менеджеров
        self.data_manager = DataManager()
        self.datasets = {}
        self.current_dataset = None
        
        # Текущий проект (для сохранения)
        self.project_path = None
        
        # Инициализация менеджера дашбордов
        self.dashboard_manager = DashboardManager()
        
        # Инициализация менеджера истории
        self.history_manager = HistoryManager()

        self.init_ui()
        
        # Сохраняем начальное состояние
        self.save_history_state()

    # =========================================================
    # UI INIT
    # =========================================================

    def init_ui(self):
        self.init_menu()
        self.init_toolbar()
        self.init_tabs()
        self.init_page_tabs()
        self.init_left()
        self.init_canvas()
        self.init_right()
        self.init_bottom()
        self.init_properties_panel()
        self.init_filter_panel()
        self.init_shortcuts()
        
        # Загружаем первый дашборд
        self.load_dashboard(0)

    # ---------------- TOOLBAR ----------------
    def init_toolbar(self):
        """Создаёт панель инструментов с кнопками быстрого доступа"""
        self.toolbar = self.addToolBar("Quick Access")
        self.toolbar.setMovable(False)
        self.toolbar.setStyleSheet("""
            QToolBar {
                spacing: 5px;
                padding: 5px;
            }
            QToolBar QToolButton {
                padding: 5px 10px;
                border-radius: 4px;
            }
            QToolBar QToolButton:hover {
                background-color: #e0e0e0;
            }
        """)
        
        # --- UNDO/REDO ---
        self.undo_btn = QAction("↩️ Undo", self)
        self.undo_btn.setToolTip("Undo (Ctrl+Z)")
        self.undo_btn.triggered.connect(self.undo_action)
        self.undo_btn.setEnabled(False)
        self.toolbar.addAction(self.undo_btn)
        
        self.redo_btn = QAction("↪️ Redo", self)
        self.redo_btn.setToolTip("Redo (Ctrl+Y)")
        self.redo_btn.triggered.connect(self.redo_action)
        self.redo_btn.setEnabled(False)
        self.toolbar.addAction(self.redo_btn)
        
        self.toolbar.addSeparator()
        
        # Кнопка загрузки данных
        load_action = QAction("📂 Load Data", self)
        load_action.setToolTip("Load CSV or Excel dataset")
        load_action.triggered.connect(self.load_dataset)
        self.toolbar.addAction(load_action)
        
        self.toolbar.addSeparator()
        
        # Кнопка сохранения проекта
        save_action = QAction("💾 Save", self)
        save_action.setToolTip("Save project (Ctrl+Shift+S)")
        save_action.triggered.connect(self.save_project)
        self.toolbar.addAction(save_action)
        
        # Кнопка загрузки проекта
        open_action = QAction("📂 Open", self)
        open_action.setToolTip("Open project (Ctrl+O)")
        open_action.triggered.connect(self.load_project)
        self.toolbar.addAction(open_action)
        
        self.toolbar.addSeparator()
        
        # --- КНОПКИ ЭКСПОРТА ---
        export_png_action = QAction("📸 Export PNG", self)
        export_png_action.setToolTip("Export entire dashboard to PNG with preview")
        export_png_action.triggered.connect(self.export_dashboard_to_png)
        self.toolbar.addAction(export_png_action)
        
        export_pdf_action = QAction("📄 Export PDF", self)
        export_pdf_action.setToolTip("Export entire dashboard to PDF with preview")
        export_pdf_action.triggered.connect(self.export_dashboard_to_pdf)
        self.toolbar.addAction(export_pdf_action)
        
        export_html_action = QAction("🌐 Export HTML", self)
        export_html_action.setToolTip("Export all pages to HTML")
        export_html_action.triggered.connect(self.export_html)
        self.toolbar.addAction(export_html_action)
        
        export_interactive_action = QAction("⚡ Interactive HTML", self)
        export_interactive_action.setToolTip("Export interactive HTML with filters")
        export_interactive_action.triggered.connect(self.export_interactive_html)
        self.toolbar.addAction(export_interactive_action)
        
        export_ppt_action = QAction("📊 Export PPT", self)
        export_ppt_action.setToolTip("Export dashboard to PowerPoint")
        export_ppt_action.triggered.connect(self.export_to_ppt)
        self.toolbar.addAction(export_ppt_action)
        
        self.toolbar.addSeparator()
        
        # Кнопка Snap
        self.snap_toggle_action = QAction("🔲 Snap", self)
        self.snap_toggle_action.setCheckable(True)
        self.snap_toggle_action.setChecked(True)
        self.snap_toggle_action.setToolTip("Toggle Snap to Grid (Ctrl+G)")
        self.snap_toggle_action.triggered.connect(self.toggle_snap)
        self.toolbar.addAction(self.snap_toggle_action)
        
        self.toolbar.addSeparator()
        
        # Кнопки шаблонов
        templates_action = QAction("📋 Templates", self)
        templates_action.setToolTip("Open template manager")
        templates_action.triggered.connect(self.show_template_dialog)
        self.toolbar.addAction(templates_action)
        
        save_template_action = QAction("💾 Save Template", self)
        save_template_action.setToolTip("Save current dashboard as template")
        save_template_action.triggered.connect(self.save_current_as_template_dialog)
        self.toolbar.addAction(save_template_action)

    # ---------------- TABS (ДАШБОРДЫ) ----------------
    def init_tabs(self):
        """Инициализирует панель вкладок дашбордов"""
        self.tab_bar = TabBar()
        self.tab_bar.tab_changed.connect(self.on_tab_changed)
        self.tab_bar.tab_added.connect(self.on_tab_added)
        self.tab_bar.tab_closed.connect(self.on_tab_closed)
        self.tab_bar.tab_renamed.connect(self.on_tab_renamed)
        
        # Устанавливаем вкладки
        names = self.dashboard_manager.get_dashboard_names()
        self.tab_bar.set_tabs(names, 0)
        
        # Добавляем в окно (вверху)
        self.tab_widget = QWidget()
        tab_layout = QVBoxLayout(self.tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(self.tab_bar)
        
        self.setMenuWidget(self.tab_widget)

    # ---------------- PAGE TABS (СТРАНИЦЫ) ----------------
    def init_page_tabs(self):
        """Инициализирует панель страниц внутри дашборда"""
        self.page_tab_bar = PageTabBar()
        self.page_tab_bar.page_changed.connect(self.on_page_changed)
        self.page_tab_bar.page_added.connect(self.on_page_added)
        self.page_tab_bar.page_closed.connect(self.on_page_closed)
        self.page_tab_bar.page_renamed.connect(self.on_page_renamed)
        
        # Создаём виджет для панели страниц
        self.page_container = QWidget()
        page_layout = QVBoxLayout(self.page_container)
        page_layout.setContentsMargins(10, 2, 10, 2)
        page_layout.addWidget(self.page_tab_bar)
        
        # Устанавливаем как док-виджет сверху
        dock = QDockWidget("Pages", self)
        dock.setWidget(self.page_container)
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        dock.setTitleBarWidget(QWidget())  # Убираем заголовок
        dock.setMinimumHeight(40)
        dock.setMaximumHeight(60)
        self.addDockWidget(Qt.TopDockWidgetArea, dock)

    # ---------------- TAB HANDLERS (ДАШБОРДЫ) ----------------
    def on_tab_changed(self, index: int):
        """Переключение на другой дашборд"""
        self.save_current_dashboard()
        self.dashboard_manager.switch_to_dashboard(index)
        self.load_dashboard(index)
        self.save_history_state()
        self.statusBar().showMessage(f"Switched to: {self.dashboard_manager.get_dashboard_names()[index]}", 2000)

    def on_tab_added(self, name: str):
        """Добавление нового дашборда"""
        self.dashboard_manager.add_dashboard(name)
        index = len(self.dashboard_manager.dashboards) - 1
        
        names = self.dashboard_manager.get_dashboard_names()
        self.tab_bar.set_tabs(names, index)
        self.load_dashboard(index)
        self.save_history_state()
        self.statusBar().showMessage(f"Created new dashboard: {name}", 2000)

    def on_tab_closed(self, index: int):
        """Закрытие дашборда"""
        name = self.dashboard_manager.dashboards[index].name
        self.dashboard_manager.remove_dashboard(index)
        
        names = self.dashboard_manager.get_dashboard_names()
        current = self.dashboard_manager.current_index
        self.tab_bar.set_tabs(names, current)
        self.load_dashboard(current)
        self.save_history_state()
        self.statusBar().showMessage(f"Closed dashboard: {name}", 2000)

    def on_tab_renamed(self, index: int, new_name: str):
        """Переименование дашборда"""
        self.dashboard_manager.dashboards[index].name = new_name
        self.save_history_state()
        self.statusBar().showMessage(f"Renamed to: {new_name}", 2000)

    # ---------------- PAGE HANDLERS (СТРАНИЦЫ) ----------------
    def on_page_changed(self, index: int):
        """Переключение на другую страницу"""
        dashboard = self.dashboard_manager.get_current_dashboard()
        dashboard.switch_to_page(index)
        self.load_current_page()
        self.save_history_state()
        self.statusBar().showMessage(f"Switched to page: {dashboard.get_page_names()[index]}", 2000)

    def on_page_added(self, name: str):
        """Добавление новой страницы"""
        dashboard = self.dashboard_manager.get_current_dashboard()
        dashboard.add_page(name)
        index = len(dashboard.pages) - 1
        self.page_tab_bar.set_pages(dashboard.get_page_names(), index)
        self.load_current_page()
        self.save_history_state()
        self.statusBar().showMessage(f"Created new page: {name}", 2000)

    def on_page_closed(self, index: int):
        """Закрытие страницы"""
        dashboard = self.dashboard_manager.get_current_dashboard()
        name = dashboard.pages[index].name
        dashboard.remove_page(index)
        current = dashboard.current_page
        self.page_tab_bar.set_pages(dashboard.get_page_names(), current)
        self.load_current_page()
        self.save_history_state()
        self.statusBar().showMessage(f"Closed page: {name}", 2000)

    def on_page_renamed(self, index: int, new_name: str):
        """Переименование страницы"""
        dashboard = self.dashboard_manager.get_current_dashboard()
        dashboard.pages[index].name = new_name
        self.save_history_state()
        self.statusBar().showMessage(f"Renamed page to: {new_name}", 2000)

    def save_current_dashboard(self):
        """Сохраняет текущее состояние дашборда (все страницы)"""
        dashboard = self.dashboard_manager.get_current_dashboard()
        
        for page in dashboard.pages:
            page.charts.clear()
        
        current_page = dashboard.get_current_page()
        for item in self.canvas.scene.items():
            if isinstance(item, PlotItem) or isinstance(item, MapItem):
                chart_config = ChartConfig(
                    chart_type=item.chart_type if hasattr(item, 'chart_type') else "map",
                    dataset_name=item.dataset_name if hasattr(item, 'dataset_name') else self.current_dataset or "",
                    x_column=item.x_column,
                    y_columns=[item.y_column],
                    aggregation=item.aggregation if hasattr(item, 'aggregation') else "none",
                    title=item.title if hasattr(item, 'title') else "",
                    color="#0078d4",
                    show_legend=True,
                    width=item.chart_width,
                    height=item.chart_height,
                    x=int(item.x()),
                    y=int(item.y()),
                    page=dashboard.current_page
                )
                current_page.add_chart(chart_config)
            elif isinstance(item, TextItem):
                chart_config = ChartConfig(
                    chart_type="text",
                    dataset_name="",
                    x_column="",
                    y_columns=[],
                    aggregation="none",
                    title=item.toPlainText() if hasattr(item, 'toPlainText') else "Text",
                    color="#333333",
                    show_legend=False,
                    width=item.chart_width if hasattr(item, 'chart_width') else 400,
                    height=item.chart_height if hasattr(item, 'chart_height') else 100,
                    x=int(item.x()),
                    y=int(item.y()),
                    page=dashboard.current_page
                )
                chart_config.text_type = "text"
                chart_config.text_content = item.toPlainText() if hasattr(item, 'toPlainText') else ""
                chart_config.font_size = item.font().pointSize() if hasattr(item, 'font') else 14
                chart_config.bold = item.font().bold() if hasattr(item, 'font') else False
                chart_config.color = item.defaultTextColor().name() if hasattr(item, 'defaultTextColor') else "#333333"
                chart_config.background_color = item.background_color if hasattr(item, 'background_color') else None
                current_page.add_chart(chart_config)
            elif isinstance(item, ShapeItem):
                chart_config = ChartConfig(
                    chart_type="shape",
                    dataset_name="",
                    x_column="",
                    y_columns=[],
                    aggregation="none",
                    title=item.shape_type if hasattr(item, 'shape_type') else "Shape",
                    color="#0078d4",
                    show_legend=False,
                    width=item.chart_width if hasattr(item, 'chart_width') else 200,
                    height=item.chart_height if hasattr(item, 'chart_height') else 150,
                    x=int(item.x()),
                    y=int(item.y()),
                    page=dashboard.current_page
                )
                chart_config.shape_type = item.shape_type if hasattr(item, 'shape_type') else "rectangle"
                chart_config.shape_color = item.color if hasattr(item, 'color') else "#0078d4"
                chart_config.shape_fill = item.fill_color if hasattr(item, 'fill_color') else None
                current_page.add_chart(chart_config)
        
        print(f"💾 Saved dashboard: {dashboard.name}")

    def load_dashboard(self, index: int):
        """Загружает дашборд"""
        if index >= len(self.dashboard_manager.dashboards):
            return
            
        dashboard = self.dashboard_manager.dashboards[index]
        
        # Очищаем сцену
        self.canvas.scene.clear()
        
        # Проверяем, есть ли датасеты
        if not self.datasets:
            print("⚠️ No datasets loaded. Load a dataset first!")
            self.statusBar().showMessage("⚠️ No datasets loaded. Click 'Load Dataset' button!", 5000)
            
            text_item = QGraphicsTextItem(
                "📂 No data loaded\n\n"
                "Click 'Load Dataset' button\n"
                "in the left panel to load\n"
                "CSV or Excel file"
            )
            text_item.setDefaultTextColor(Qt.gray)
            text_item.setPos(200, 200)
            self.canvas.scene.addItem(text_item)
            
            self.canvas.update_scene_size()
            return
        
        # Настраиваем фильтры для текущего датасета
        if self.current_dataset and self.current_dataset in self.datasets:
            df = self.datasets[self.current_dataset]
            self.filter_panel.set_dataset(df, self.current_dataset)
        
        # Обновляем панель страниц
        self.page_tab_bar.set_pages(dashboard.get_page_names(), dashboard.current_page)
        
        # Загружаем текущую страницу
        self.load_current_page()
        
        print(f"✅ Loaded dashboard: {dashboard.name} ({len(dashboard.pages)} pages)")

    def load_current_page(self):
        """Загружает текущую страницу"""
        dashboard = self.dashboard_manager.get_current_dashboard()
        page = dashboard.get_current_page()
        
        # Очищаем сцену
        self.canvas.scene.clear()
        
        if not self.datasets:
            return
        
        restored_count = 0
        for chart_config in page.charts:
            try:
                if chart_config.chart_type == "text":
                    self._restore_text_chart(chart_config)
                    restored_count += 1
                elif chart_config.chart_type == "shape":
                    self._restore_shape_chart(chart_config)
                    restored_count += 1
                else:
                    if chart_config.dataset_name not in self.datasets:
                        # Пробуем использовать текущий датасет
                        if self.current_dataset in self.datasets:
                            chart_config.dataset_name = self.current_dataset
                        else:
                            continue
                    
                    df = self.datasets[chart_config.dataset_name]
                    if chart_config.x_column not in df.columns:
                        continue
                    
                    valid_y_columns = [col for col in chart_config.y_columns if col in df.columns]
                    if not valid_y_columns:
                        continue
                    
                    self._restore_chart(chart_config)
                    restored_count += 1
                
            except Exception as e:
                print(f"❌ Error restoring chart: {e}")
        
        if self.filter_panel.get_active_filters():
            self.apply_filters_to_charts(self.filter_panel.get_active_filters())
        
        self.canvas.update_scene_size()
        print(f"✅ Loaded page: {page.name} ({restored_count} charts)")

    def _restore_chart(self, config: ChartConfig):
        """Восстанавливает график из конфигурации"""
        df = self.datasets[config.dataset_name]
        
        try:
            if config.chart_type == "map":
                item = MapItem(
                    dataframe=df,
                    x_column=config.x_column,
                    y_column=config.y_columns[0] if config.y_columns else "",
                    title=config.title,
                    width=config.width,
                    height=config.height,
                )
            else:
                item = PlotItem(
                    dataframe=df,
                    chart_type=config.chart_type,
                    x_column=config.x_column,
                    y_columns=config.y_columns,
                    aggregation=config.aggregation,
                    title=config.title,
                    color=config.color,
                    show_legend=config.show_legend,
                    width=config.width,
                    height=config.height,
                )
            
            # Восстанавливаем датасет
            item.dataset_name = config.dataset_name
            
            item.setPos(config.x, config.y)
            self.canvas.scene.addItem(item)
            
        except Exception as e:
            print(f"❌ Error restoring chart: {e}")

    def _restore_text_chart(self, config: ChartConfig):
        """Восстанавливает текстовый блок из конфигурации"""
        try:
            item = TextItem(
                text=config.text_content if hasattr(config, 'text_content') else "Text",
                text_type=config.text_type if hasattr(config, 'text_type') else "text",
                font_size=config.font_size if hasattr(config, 'font_size') else 14,
                bold=config.bold if hasattr(config, 'bold') else False,
                color=config.color if hasattr(config, 'color') else "#333333",
                background_color=config.background_color if hasattr(config, 'background_color') else None,
                width=config.width,
                height=config.height,
            )
            
            item.setPos(config.x, config.y)
            self.canvas.scene.addItem(item)
        except Exception as e:
            print(f"❌ Error restoring text: {e}")

    def _restore_shape_chart(self, config: ChartConfig):
        """Восстанавливает фигуру из конфигурации"""
        try:
            colors = {
                "rectangle": "#0078d4",
                "circle": "#d4380d",
                "line": "#333333",
                "arrow": "#d4a00d",
            }
            
            fill_colors = {
                "rectangle": "#e6f2ff",
                "circle": "#ffe6e6",
                "line": None,
                "arrow": None,
            }
            
            shape_type = config.shape_type if hasattr(config, 'shape_type') else "rectangle"
            
            item = ShapeItem(
                shape_type=shape_type,
                width=config.width,
                height=config.height,
                color=config.shape_color if hasattr(config, 'shape_color') else colors.get(shape_type, "#0078d4"),
                fill_color=config.shape_fill if hasattr(config, 'shape_fill') else fill_colors.get(shape_type, None),
                line_width=2,
            )
            
            item.setPos(config.x, config.y)
            self.canvas.scene.addItem(item)
        except Exception as e:
            print(f"❌ Error restoring shape: {e}")

    # ---------------- MENU ----------------
    def init_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        
        load_action = file_menu.addAction("Load dataset")
        load_action.triggered.connect(self.load_dataset)
        
        file_menu.addSeparator()
        
        save_action = file_menu.addAction("Save project")
        save_action.triggered.connect(self.save_project)
        
        load_project_action = file_menu.addAction("Load project")
        load_project_action.triggered.connect(self.load_project)
        
        file_menu.addSeparator()
        
        export_menu = file_menu.addMenu("Export")
        
        export_png_action = export_menu.addAction("📸 Export Dashboard to PNG")
        export_png_action.triggered.connect(self.export_dashboard_to_png)
        
        export_pdf_action = export_menu.addAction("📄 Export Dashboard to PDF")
        export_pdf_action.triggered.connect(self.export_dashboard_to_pdf)
        
        export_menu.addSeparator()
        
        export_html_action = export_menu.addAction("🌐 Export to HTML")
        export_html_action.triggered.connect(self.export_html)
        
        export_interactive_action = export_menu.addAction("⚡ Interactive HTML")
        export_interactive_action.triggered.connect(self.export_interactive_html)
        
        export_ppt_action = export_menu.addAction("📊 Export to PowerPoint")
        export_ppt_action.triggered.connect(self.export_to_ppt)

    # ---------------- LEFT PANEL ----------------
    def init_left(self):
        self.dataset_selector = QComboBox()
        self.dataset_selector.currentTextChanged.connect(self.on_dataset_change)

        self.x_selector = QComboBox()
        self.y_selector = QComboBox()

        layout = QVBoxLayout()
        
        load_btn = QPushButton("📂 Load Dataset")
        load_btn.setObjectName("loadBtn")
        load_btn.setStyleSheet("""
            QPushButton#loadBtn {
                background-color: #0078d4;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 4px;
                border: none;
                font-size: 14px;
            }
            QPushButton#loadBtn:hover {
                background-color: #005a9e;
            }
            QPushButton#loadBtn:pressed {
                background-color: #003d6b;
            }
        """)
        load_btn.clicked.connect(self.load_dataset)
        layout.addWidget(load_btn)
        
        layout.addSpacing(10)
        
        dataset_label = QLabel("DATASET")
        dataset_label.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(dataset_label)
        layout.addWidget(self.dataset_selector)
        
        layout.addSpacing(10)
        
        x_label = QLabel("X axis")
        x_label.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(x_label)
        layout.addWidget(self.x_selector)
        
        y_label = QLabel("Y axis")
        y_label.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(y_label)
        layout.addWidget(self.y_selector)
        
        layout.addStretch()

        container = QWidget()
        container.setLayout(layout)

        dock = QDockWidget("Controls", self)
        dock.setWidget(container)
        dock.setMinimumWidth(250)

        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    # ---------------- CANVAS ----------------
    def init_canvas(self):
        self.canvas = GridCanvas(grid_size=20)
        self.setCentralWidget(self.canvas)
        
        self.snap_action = QAction("Toggle Snap", self)
        self.snap_action.setShortcut("Ctrl+G")
        self.snap_action.triggered.connect(self.toggle_snap)
        self.addAction(self.snap_action)
        
        self.statusBar().showMessage("Snap to Grid: ON (Ctrl+G to toggle)", 3000)

    def toggle_snap(self):
        state = self.canvas.toggle_snap()
        self.statusBar().showMessage(f"Snap to Grid: {'ON' if state else 'OFF'}", 2000)
        
        if hasattr(self, 'snap_toggle_action'):
            self.snap_toggle_action.setChecked(state)

    # ---------------- RIGHT PANEL ----------------
    def init_right(self):
        self.table = QTableWidget()

        dock = QDockWidget("Dataset Info", self)
        dock.setWidget(self.table)
        dock.setMinimumWidth(320)

        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    # ---------------- BOTTOM CHART GALLERY ----------------
    def init_bottom(self):
        self.tabs = QTabWidget()
        
        # Основные графики
        basic_tab = QWidget()
        basic_layout = QHBoxLayout(basic_tab)
        basic_layout.setContentsMargins(5, 5, 5, 5)
        
        chart_types = ["line", "scatter", "bar", "area", "pie", "donut", "histogram", "boxplot", "heatmap", "map"]
        for chart_type in chart_types:
            btn = self.create_chart_button(chart_type)
            basic_layout.addWidget(btn)
        
        basic_layout.addStretch()
        self.tabs.addTab(basic_tab, "Basic")
        
        # Дополнительные графики
        advanced_tab = QWidget()
        advanced_layout = QHBoxLayout(advanced_tab)
        advanced_layout.setContentsMargins(5, 5, 5, 5)
        
        advanced_charts = ["treemap", "funnel", "gauge", "waterfall"]
        for chart_type in advanced_charts:
            btn = self.create_chart_button(chart_type)
            advanced_layout.addWidget(btn)
        
        advanced_layout.addStretch()
        self.tabs.addTab(advanced_tab, "Advanced")
        
        # Текстовые блоки
        text_tab = QWidget()
        text_layout = QHBoxLayout(text_tab)
        text_layout.setContentsMargins(5, 5, 5, 5)
        
        text_btn = QPushButton("📝 Text")
        text_btn.setFixedSize(140, 60)
        text_btn.clicked.connect(lambda: self.create_text_item("text"))
        text_layout.addWidget(text_btn)
        
        title_btn = QPushButton("📰 Title")
        title_btn.setFixedSize(140, 60)
        title_btn.clicked.connect(lambda: self.create_text_item("title"))
        text_layout.addWidget(title_btn)
        
        html_btn = QPushButton("🌐 HTML")
        html_btn.setFixedSize(140, 60)
        html_btn.clicked.connect(lambda: self.create_text_item("html"))
        text_layout.addWidget(html_btn)
        
        text_layout.addStretch()
        self.tabs.addTab(text_tab, "Text")
        
        # Фигуры
        shapes_tab = QWidget()
        shapes_layout = QHBoxLayout(shapes_tab)
        shapes_layout.setContentsMargins(5, 5, 5, 5)
        
        shape_configs = [
            ("rectangle", "⬜ Rectangle", 200, 150),
            ("circle", "⭕ Circle", 180, 180),
            ("line", "━ Line", 250, 50),
            ("arrow", "➡ Arrow", 250, 60),
        ]
        
        for shape_type, label, width, height in shape_configs:
            btn = QPushButton(label)
            btn.setFixedSize(140, 60)
            btn.clicked.connect(lambda checked, st=shape_type, w=width, h=height: 
                               self.create_shape_item(st, w, h))
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 11px;
                    font-weight: bold;
                    background-color: #f0f0f0;
                    border: 2px solid #ddd;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                    border-color: #0078d4;
                }
            """)
            shapes_layout.addWidget(btn)
        
        shapes_layout.addStretch()
        self.tabs.addTab(shapes_tab, "Shapes")

        dock = QDockWidget("Chart Gallery", self)
        dock.setWidget(self.tabs)
        dock.setMinimumHeight(160)

        self.addDockWidget(Qt.BottomDockWidgetArea, dock)

    def create_chart_button(self, chart_type):
        """Создаёт кнопку для типа графика с миниатюрой"""
        btn = QPushButton()
        btn.setFixedSize(140, 80)
        btn.clicked.connect(lambda: self.create_chart(chart_type))
        
        # Генерируем миниатюру
        pixmap = ChartThumbnailGenerator.generate_thumbnail(chart_type, 140, 60)
        
        # Создаём иконку из пиксмапа
        icon = QIcon(pixmap)
        btn.setIcon(icon)
        btn.setIconSize(pixmap.size())
        
        # Добавляем текст
        btn.setText(f"\n{chart_type.upper()}")
        btn.setStyleSheet("""
            QPushButton {
                font-size: 10px;
                font-weight: bold;
                background-color: #f0f0f0;
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 4px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #0078d4;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        
        return btn

    # ---------------- PROPERTIES PANEL ----------------
    def init_properties_panel(self):
        self.properties_panel = PropertiesPanel()
        self.properties_panel.set_main_window(self)
        self.properties_panel.set_datasets(self.datasets)
        self.properties_panel.property_changed.connect(self.on_properties_changed)
        self.properties_panel.apply_clicked.connect(self.on_apply_clicked)
        
        dock = QDockWidget("Properties", self)
        dock.setWidget(self.properties_panel)
        dock.setMinimumWidth(350)
        
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    # ---------------- FILTER PANEL ----------------
    def init_filter_panel(self):
        self.filter_panel = FilterPanel()
        self.filter_panel.filter_changed.connect(self.on_filters_changed)
        
        dock = QDockWidget("Filters", self)
        dock.setWidget(self.filter_panel)
        dock.setMinimumWidth(250)
        dock.setMaximumHeight(400)
        
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    # ---------------- SHORTCUTS ----------------
    def init_shortcuts(self):
        undo_action = QAction("Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo_action)
        self.addAction(undo_action)
        
        redo_action = QAction("Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo_action)
        self.addAction(redo_action)
        
        save_as_action = QAction("Save As", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_project)
        self.addAction(save_as_action)
        
        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.load_project)
        self.addAction(open_action)

    # =========================================================
    # DATA LOADING
    # =========================================================

    def load_dataset(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load dataset", "", "Data (*.csv *.xlsx)"
        )

        if not path:
            return

        try:
            df = self.data_manager.load_file(path)
            name = path.split("/")[-1]
            
            rows = len(df)
            cols = len(df.columns)
            print(f"✅ Loaded dataset: {name} ({rows} rows, {cols} columns)")
            
            self.datasets[name] = df
            
            # Обновляем селектор датасета
            self.dataset_selector.clear()
            for dataset_name in self.datasets.keys():
                self.dataset_selector.addItem(dataset_name)
            
            # Выбираем последний загруженный
            self.dataset_selector.setCurrentText(name)
            self.set_dataset(name)
            
            # Обновляем фильтры
            self.filter_panel.set_dataset(df, name)
            
            # Обновляем панель свойств
            self.properties_panel.set_datasets(self.datasets)
            
            self.statusBar().showMessage(f"✅ Loaded dataset: {name} ({rows} rows)", 3000)
            
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            self.statusBar().showMessage(f"Error loading dataset: {e}", 5000)

    # =========================================================
    # DATASET SWITCH
    # =========================================================

    def on_dataset_change(self, name):
        self.set_dataset(name)

    def set_dataset(self, name):
        if name not in self.datasets:
            return

        self.current_dataset = name
        df = self.datasets[name]

        self.x_selector.clear()
        self.y_selector.clear()

        for col in df.columns:
            self.x_selector.addItem(col)
            self.y_selector.addItem(col)

        self.update_table(df)
        
        self.statusBar().showMessage(f"Dataset: {name} ({len(df)} rows, {len(df.columns)} columns)")

    # =========================================================
    # INFO TABLE
    # =========================================================

    def update_table(self, df):
        self.table.clear()
        self.table.setRowCount(len(df.columns))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Column", "Type", "Non-null"])

        for i, col in enumerate(df.columns):
            self.table.setItem(i, 0, QTableWidgetItem(str(col)))
            self.table.setItem(i, 1, QTableWidgetItem(str(df[col].dtype)))
            self.table.setItem(i, 2, QTableWidgetItem(str(df[col].notna().sum())))

    # =========================================================
    # FILTER HANDLERS
    # =========================================================

    def on_filters_changed(self, filters: dict):
        print(f"🔍 Filters changed: {filters}")
        self.apply_filters_to_charts(filters)
        self.save_history_state()

    def apply_filters_to_charts(self, filters: dict):
        if not self.current_dataset or self.current_dataset not in self.datasets:
            return
        
        df = self.datasets[self.current_dataset]
        filtered_df = self.filter_panel.apply_filters(df)
        
        for item in self.canvas.scene.items():
            if isinstance(item, PlotItem):
                item.df = filtered_df
                item.build_chart()
            elif isinstance(item, MapItem):
                item.df = filtered_df
                item.build_map()

    # =========================================================
    # PROPERTIES HANDLERS
    # =========================================================

    def on_apply_clicked(self):
        self.statusBar().showMessage("✅ Properties applied", 2000)

    def on_properties_changed(self, properties: dict):
        item = self.properties_panel.current_item
        if not item or not isinstance(item, PlotItem):
            return
        
        try:
            # Проверяем, изменился ли датасет
            new_dataset = properties.get("dataset_name", "")
            if new_dataset and new_dataset in self.datasets:
                # Меняем датасет
                df = self.datasets[new_dataset]
                item.df = df
                item.dataset_name = new_dataset
            
            # Обновляем остальные свойства
            item.update_properties(properties)
            
            # Обновляем конфигурацию в дашборде
            dashboard = self.dashboard_manager.get_current_dashboard()
            current_page = dashboard.get_current_page()
            for chart_config in current_page.charts:
                if (abs(chart_config.x - item.x()) < 10 and 
                    abs(chart_config.y - item.y()) < 10):
                    chart_config.dataset_name = new_dataset if new_dataset else chart_config.dataset_name
                    chart_config.y_columns = properties.get("y_columns", [])
                    chart_config.aggregation = properties.get("aggregation", "none")
                    chart_config.title = properties.get("title", "")
                    chart_config.color = properties.get("color", "#0078d4")
                    chart_config.show_legend = properties.get("show_legend", True)
                    chart_config.width = properties.get("width", item.chart_width)
                    chart_config.height = properties.get("height", item.chart_height)
                    break
            
            self.save_history_state()
            self.statusBar().showMessage("✅ Properties applied", 2000)
            
        except Exception as e:
            print(f"❌ Error applying properties: {e}")
            self.statusBar().showMessage(f"Error: {e}", 5000)

    # =========================================================
    # CHART ENGINE
    # =========================================================

    def create_chart(self, chart_type):
        print(f"🔥 CREATE CHART: {chart_type}")

        if self.current_dataset is None:
            self.statusBar().showMessage("⚠️ Please load a dataset first!", 3000)
            return

        df = self.datasets.get(self.current_dataset)
        if df is None:
            self.statusBar().showMessage(f"⚠️ Dataset '{self.current_dataset}' not found!", 3000)
            return

        x_col = self.x_selector.currentText()
        y_col = self.y_selector.currentText()

        if not x_col or not y_col:
            self.statusBar().showMessage("⚠️ Please select X and Y columns!", 3000)
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        try:
            width, height = self._get_chart_size(chart_type)

            if len(df) == 0:
                self.statusBar().showMessage("Dataset is empty!", 3000)
                return

            filtered_df = self.filter_panel.apply_filters(df)

            if chart_type == "map":
                item = MapItem(
                    dataframe=filtered_df,
                    x_column=x_col,
                    y_column=y_col,
                    title=f"Map: {y_col} vs {x_col}",
                    width=width,
                    height=height,
                )
            else:
                item = PlotItem(
                    dataframe=filtered_df,
                    chart_type=chart_type,
                    x_column=x_col,
                    y_columns=[y_col],
                    aggregation="none",
                    title=f"{chart_type.upper()}: {y_col} vs {x_col}",
                    color="#0078d4",
                    show_legend=True,
                    width=width,
                    height=height,
                )
            
            # СОХРАНЯЕМ ДАТАСЕТ В ГРАФИКЕ
            item.dataset_name = self.current_dataset

            self.canvas.scene.addItem(item)
            
            offset = len(self.canvas.scene.items()) * 25
            snapped_pos = self.canvas.snap_to_grid(QPoint(int(50 + offset), int(50 + offset)))
            item.setPos(snapped_pos.x(), snapped_pos.y())
            
            self.canvas.update_scene_size()
            self.update_selection_info(item)
            
            # СОХРАНЯЕМ В ДАШБОРД
            dashboard = self.dashboard_manager.get_current_dashboard()
            current_page = dashboard.get_current_page()
            chart_config = ChartConfig(
                chart_type=chart_type,
                dataset_name=self.current_dataset,
                x_column=x_col,
                y_columns=[y_col],
                aggregation="none",
                title=f"{chart_type.upper()}: {y_col} vs {x_col}",
                color="#0078d4",
                show_legend=True,
                width=width,
                height=height,
                x=int(item.x()),
                y=int(item.y()),
                page=dashboard.current_page
            )
            current_page.add_chart(chart_config)
            
            self.save_history_state()
            self.statusBar().showMessage(f"✅ Chart added to {dashboard.name} - {current_page.name}", 2000)
            
        except Exception as e:
            print(f"❌ Error creating chart: {e}")
            import traceback
            traceback.print_exc()
            self.statusBar().showMessage(f"Error: {e}", 5000)
            
        finally:
            QApplication.restoreOverrideCursor()

    def _get_chart_size(self, chart_type):
        """Возвращает размеры для разных типов графиков"""
        if chart_type == "map":
            return 700, 500
        elif chart_type in ["histogram", "boxplot"]:
            return 500, 400
        elif chart_type == "pie":
            return 500, 500
        elif chart_type == "donut":
            return 500, 500
        elif chart_type == "heatmap":
            return 550, 450
        elif chart_type == "bar":
            return 600, 400
        elif chart_type in ["treemap", "funnel", "gauge", "waterfall"]:
            return 550, 400
        else:
            return 600, 350

    # =========================================================
    # TEXT ITEMS
    # =========================================================

    def create_text_item(self, text_type="text"):
        """Создаёт текстовый блок на дашборде"""
        print(f"📝 CREATE TEXT: {text_type}")
        
        if text_type == "title":
            text = "📊 Dashboard Title"
            font_size = 24
            bold = True
            color = "#1a1a2e"
            background_color = None
            width = 600
            height = 80
        elif text_type == "html":
            text = "📊 Dashboard Report\nGenerated: 2024-01-01\nClick on charts to filter data"
            font_size = 14
            bold = False
            color = "#333333"
            background_color = None
            width = 500
            height = 150
        else:
            text = "Double-click to edit text"
            font_size = 14
            bold = False
            color = "#333333"
            background_color = None
            width = 400
            height = 100
        
        item = TextItem(
            text=text,
            text_type=text_type,
            font_size=font_size,
            bold=bold,
            color=color,
            background_color=background_color,
            width=width,
            height=height,
        )
        
        self.canvas.scene.addItem(item)
        
        offset = len(self.canvas.scene.items()) * 25
        snapped_pos = self.canvas.snap_to_grid(QPoint(int(50 + offset), int(50 + offset)))
        item.setPos(snapped_pos.x(), snapped_pos.y())
        
        # СОХРАНЯЕМ В ДАШБОРД
        dashboard = self.dashboard_manager.get_current_dashboard()
        current_page = dashboard.get_current_page()
        chart_config = ChartConfig(
            chart_type="text",
            dataset_name="",
            x_column="",
            y_columns=[],
            aggregation="none",
            title=text,
            color="#333333",
            show_legend=False,
            width=width,
            height=height,
            x=int(item.x()),
            y=int(item.y()),
            page=dashboard.current_page
        )
        chart_config.text_type = text_type
        chart_config.text_content = text
        chart_config.font_size = font_size
        chart_config.bold = bold
        chart_config.color = color
        chart_config.background_color = background_color
        current_page.add_chart(chart_config)
        
        self.canvas.update_scene_size()
        self.save_history_state()
        
        self.statusBar().showMessage(f"✅ Text added", 2000)
        print(f"✅ Text added")

    # =========================================================
    # SHAPES
    # =========================================================

    def create_shape_item(self, shape_type, width, height):
        """Создаёт геометрическую фигуру"""
        from ui.shape_item import ShapeItem
        
        colors = {
            "rectangle": "#0078d4",
            "circle": "#d4380d",
            "line": "#333333",
            "arrow": "#d4a00d",
        }
        
        fill_colors = {
            "rectangle": "#e6f2ff",
            "circle": "#ffe6e6",
            "line": None,
            "arrow": None,
        }
        
        item = ShapeItem(
            shape_type=shape_type,
            width=width,
            height=height,
            color=colors.get(shape_type, "#0078d4"),
            fill_color=fill_colors.get(shape_type, None),
            line_width=2,
        )
        
        self.canvas.scene.addItem(item)
        
        offset = len(self.canvas.scene.items()) * 25
        snapped_pos = self.canvas.snap_to_grid(QPoint(int(50 + offset), int(50 + offset)))
        item.setPos(snapped_pos.x(), snapped_pos.y())
        
        # СОХРАНЯЕМ В ДАШБОРД
        dashboard = self.dashboard_manager.get_current_dashboard()
        current_page = dashboard.get_current_page()
        chart_config = ChartConfig(
            chart_type="shape",
            dataset_name="",
            x_column="",
            y_columns=[],
            aggregation="none",
            title=shape_type,
            color="#0078d4",
            show_legend=False,
            width=width,
            height=height,
            x=int(item.x()),
            y=int(item.y()),
            page=dashboard.current_page
        )
        chart_config.shape_type = shape_type
        chart_config.shape_color = colors.get(shape_type, "#0078d4")
        chart_config.shape_fill = fill_colors.get(shape_type, None)
        current_page.add_chart(chart_config)
        
        self.canvas.update_scene_size()
        self.save_history_state()
        
        self.statusBar().showMessage(f"✅ Shape added", 2000)
        print(f"✅ Shape added")

    def update_selection_info(self, item):
        if isinstance(item, PlotItem) or isinstance(item, MapItem):
            self.properties_panel.current_item = item
            
            # Обновляем список датасетов
            self.properties_panel.set_datasets(self.datasets)
            
            df = item.df
            x_col = item.x_column
            
            # Обновляем колонки для Y (все кроме X)
            columns = [col for col in df.columns if col != x_col]
            self.properties_panel.set_columns(columns)
            
            # Загружаем текущие свойства
            properties = {
                "dataset_name": item.dataset_name if hasattr(item, 'dataset_name') else self.current_dataset or "",
                "y_columns": item.y_columns if hasattr(item, 'y_columns') else [],
                "aggregation": item.aggregation if hasattr(item, 'aggregation') else "none",
                "title": item.title if hasattr(item, 'title') else "",
                "color": "#0078d4",
                "show_legend": True,
                "width": item.chart_width,
                "height": item.chart_height
            }
            self.properties_panel.set_properties(properties)

    def delete_selected_chart(self):
        selected = self.canvas.scene.selectedItems()
        count = 0
        
        dashboard = self.dashboard_manager.get_current_dashboard()
        current_page = dashboard.get_current_page()
        
        for item in selected:
            if isinstance(item, PlotItem) or isinstance(item, MapItem) or isinstance(item, TextItem) or isinstance(item, ShapeItem):
                self.canvas.scene.removeItem(item)
                
                for chart_config in current_page.charts[:]:
                    if (abs(chart_config.x - item.x()) < 10 and 
                        abs(chart_config.y - item.y()) < 10):
                        current_page.charts.remove(chart_config)
                        break
                
                count += 1
                print(f"🗑️ Item deleted")
        
        self.canvas.update_scene_size()
        self.save_history_state()
        
        if count == 0:
            self.properties_panel.current_item = None
            self.statusBar().showMessage("No item selected", 2000)
        else:
            self.properties_panel.current_item = None
            self.statusBar().showMessage(f"Deleted {count} item(s)", 2000)

    def export_selected_chart(self):
        selected = self.canvas.scene.selectedItems()
        
        for item in selected:
            if isinstance(item, PlotItem) or isinstance(item, MapItem) or isinstance(item, TextItem) or isinstance(item, ShapeItem):
                path, _ = QFileDialog.getSaveFileName(
                    self, "Export chart", "", "PNG (*.png)"
                )
                if path:
                    try:
                        item.export_to_png(path, scale=2)
                        self.statusBar().showMessage(f"✅ Exported to {path}", 3000)
                    except Exception as e:
                        self.statusBar().showMessage(f"Error exporting: {e}", 3000)
                return
        
        self.statusBar().showMessage("Select a chart first!", 2000)

    # =========================================================
    # CHART CLICK HANDLER
    # =========================================================

    def on_chart_clicked(self, x_column: str, x_value, y_column: str = None, y_value = None):
        print(f"🔗 Chart clicked: {x_column}={x_value}")
        
        current_filters = self.filter_panel.get_active_filters()
        
        if x_column in current_filters:
            if str(x_value) not in current_filters[x_column]:
                current_filters[x_column].append(str(x_value))
        else:
            current_filters[x_column] = [str(x_value)]
        
        self.filter_panel.filter_changed.emit(current_filters)
        self.filter_panel.set_active_filters(current_filters)
        
        self.save_history_state()
        self.statusBar().showMessage(f"🔍 Filtered by: {x_column} = {x_value}", 3000)

    # =========================================================
    # TEMPLATES
    # =========================================================
    
    def show_template_dialog(self):
        """Показывает диалог управления шаблонами"""
        templates = TemplateManager.get_templates()
        
        dialog = TemplateDialog(templates, self)
        dialog.template_applied.connect(self.apply_template)
        
        if dialog.exec() == QDialog.Accepted:
            self.refresh_templates()
    
    def refresh_templates(self):
        """Обновляет список шаблонов"""
        self.statusBar().showMessage("✅ Templates refreshed", 2000)
    
    def save_current_as_template_dialog(self):
        """Сохраняет текущий дашборд как шаблон"""
        name, ok = QInputDialog.getText(
            self, "Save Template", 
            "Enter template name:"
        )
        if not ok or not name:
            return
        
        description, ok = QInputDialog.getText(
            self, "Save Template",
            "Enter template description:"
        )
        if not ok:
            return
        
        self.save_current_as_template(name, description)
    
    def save_current_as_template(self, name: str, description: str):
        """Сохраняет текущий дашборд как шаблон"""
        # Сохраняем текущий дашборд
        self.save_current_dashboard()
        
        # Получаем данные дашборда
        dashboard = self.dashboard_manager.get_current_dashboard()
        dashboard_data = dashboard.to_dict()
        
        # Сохраняем как шаблон
        success = TemplateManager.save_template(name, description, dashboard_data)
        
        if success:
            self.statusBar().showMessage(f"✅ Template '{name}' saved", 3000)
            self.refresh_templates()
        else:
            self.statusBar().showMessage(f"❌ Failed to save template", 3000)
    
    def apply_template(self, filename: str):
        """Применяет шаблон к текущему дашборду"""
        try:
            # Загружаем шаблон
            template_data = TemplateManager.load_template(filename)
            
            if not template_data:
                self.statusBar().showMessage("❌ Failed to load template", 3000)
                return
            
            # Применяем к текущему дашборду
            dashboard = self.dashboard_manager.get_current_dashboard()
            count = TemplateManager.apply_template(template_data, dashboard)
            
            if count > 0:
                # Обновляем UI
                self.page_tab_bar.set_pages(dashboard.get_page_names(), dashboard.current_page)
                self.load_current_page()
                self.save_history_state()
                self.statusBar().showMessage(f"✅ Template applied: {count} pages", 3000)
            else:
                self.statusBar().showMessage("⚠️ No pages in template", 3000)
                
        except Exception as e:
            print(f"❌ Error applying template: {e}")
            import traceback
            traceback.print_exc()
            self.statusBar().showMessage(f"Error applying template: {e}", 5000)

    # =========================================================
    # EXPORT DASHBOARD
    # =========================================================

    def export_dashboard_to_png(self):
        items = [item for item in self.canvas.scene.items() if isinstance(item, (PlotItem, MapItem, TextItem, ShapeItem))]
        if not items:
            self.statusBar().showMessage("⚠️ No items to export", 3000)
            return
        
        dialog = ExportPreviewDialog(self.canvas.scene, self)
        if dialog.exec() != QDialog.Accepted:
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Dashboard", "", "PNG (*.png)"
        )
        if not path:
            return
        
        try:
            width, height = dialog.get_export_size()
            
            from PySide6.QtGui import QPixmap, QPainter
            
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.white)
            
            painter = QPainter(pixmap)
            self.canvas.scene.render(painter)
            painter.end()
            
            pixmap.save(path, "PNG")
            
            self.statusBar().showMessage(f"✅ Dashboard exported to {path}", 3000)
            print(f"✅ Dashboard exported to {path}")
            
        except Exception as e:
            print(f"❌ Error exporting dashboard: {e}")
            self.statusBar().showMessage(f"Error exporting: {e}", 5000)

    def export_dashboard_to_pdf(self):
        items = [item for item in self.canvas.scene.items() if isinstance(item, (PlotItem, MapItem, TextItem, ShapeItem))]
        if not items:
            self.statusBar().showMessage("⚠️ No items to export", 3000)
            return
        
        dialog = ExportPreviewDialog(self.canvas.scene, self)
        if dialog.exec() != QDialog.Accepted:
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Dashboard to PDF", "", "PDF (*.pdf)"
        )
        if not path:
            return
        
        try:
            width, height = dialog.get_export_size()
            
            from PySide6.QtGui import QPixmap, QPainter, QPdfWriter
            from PySide6.QtCore import QPageSize
            
            pixmap = QPixmap(width, height)
            pixmap.fill(Qt.white)
            
            painter = QPainter(pixmap)
            self.canvas.scene.render(painter)
            painter.end()
            
            writer = QPdfWriter(path)
            page_size = QPageSize(QPageSize.A3)
            writer.setPageSize(page_size)
            writer.setPageMargins(20, 20, 20, 20)
            
            pdf_painter = QPainter(writer)
            page_rect = writer.pageRect()
            
            scale_x = page_rect.width() / pixmap.width()
            scale_y = page_rect.height() / pixmap.height()
            scale = min(scale_x, scale_y)
            
            new_width = pixmap.width() * scale
            new_height = pixmap.height() * scale
            x_offset = (page_rect.width() - new_width) / 2
            y_offset = (page_rect.height() - new_height) / 2
            
            pdf_painter.drawPixmap(
                int(x_offset), 
                int(y_offset), 
                int(new_width), 
                int(new_height), 
                pixmap
            )
            pdf_painter.end()
            
            self.statusBar().showMessage(f"✅ Dashboard exported to {path}", 3000)
            print(f"✅ Dashboard exported to {path}")
            
        except Exception as e:
            print(f"❌ Error exporting dashboard to PDF: {e}")
            self.statusBar().showMessage(f"Error exporting: {e}", 5000)

    # =========================================================
    # EXPORT TO POWERPOINT
    # =========================================================

    def export_to_ppt(self):
        """Экспортирует дашборд в PowerPoint"""
        items = [item for item in self.canvas.scene.items() 
                if isinstance(item, (PlotItem, MapItem, TextItem, ShapeItem))]
        if not items:
            self.statusBar().showMessage("⚠️ No items to export", 3000)
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, "Export to PowerPoint", "", "PowerPoint (*.pptx)"
        )
        if not path:
            return
        
        try:
            dashboard = self.dashboard_manager.get_current_dashboard()
            title = f"{dashboard.name} - Dashboard Report"
            
            from core.ppt_exporter import PPTExporter
            success = PPTExporter.export(self.canvas.scene, path, title)
            
            if success:
                self.statusBar().showMessage(f"✅ Exported to {path}", 3000)
            else:
                self.statusBar().showMessage("❌ Failed to export to PowerPoint", 3000)
                
        except Exception as e:
            print(f"❌ Error exporting to PowerPoint: {e}")
            import traceback
            traceback.print_exc()
            self.statusBar().showMessage(f"Error exporting: {e}", 5000)

    # =========================================================
    # EXPORT HTML (СТАТИЧНЫЙ)
    # =========================================================

    def export_html(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export to HTML", "", "HTML (*.html)"
        )
        if not path:
            return
        
        try:
            dashboard = self.dashboard_manager.get_current_dashboard()
            
            total_charts = 0
            for page in dashboard.pages:
                total_charts += len(page.charts)
            
            if total_charts == 0:
                self.statusBar().showMessage("⚠️ No charts to export", 3000)
                return
            
            import tempfile
            import os
            import base64
            
            temp_dir = tempfile.mkdtemp()
            pages_data = []
            
            for page_idx, page in enumerate(dashboard.pages):
                page_charts = []
                
                for chart_config in page.charts:
                    try:
                        if chart_config.chart_type in ["text", "shape"]:
                            continue
                        
                        if chart_config.dataset_name not in self.datasets:
                            continue
                        
                        df = self.datasets[chart_config.dataset_name]
                        if chart_config.x_column not in df.columns:
                            continue
                        
                        valid_y_columns = [col for col in chart_config.y_columns if col in df.columns]
                        if not valid_y_columns:
                            continue
                        
                        if chart_config.chart_type == "map":
                            temp_item = MapItem(
                                dataframe=df,
                                x_column=chart_config.x_column,
                                y_column=chart_config.y_columns[0] if chart_config.y_columns else "",
                                title=chart_config.title,
                                width=chart_config.width,
                                height=chart_config.height,
                            )
                        else:
                            temp_item = PlotItem(
                                dataframe=df,
                                chart_type=chart_config.chart_type,
                                x_column=chart_config.x_column,
                                y_columns=valid_y_columns,
                                aggregation=chart_config.aggregation,
                                title=chart_config.title,
                                color=chart_config.color,
                                show_legend=chart_config.show_legend,
                                width=chart_config.width,
                                height=chart_config.height,
                            )
                        
                        img_path = os.path.join(temp_dir, f"page_{page_idx}_chart_{len(page_charts)}.png")
                        temp_item.export_to_png(img_path, scale=1.5)
                        
                        with open(img_path, "rb") as f:
                            img_data = base64.b64encode(f.read()).decode()
                            page_charts.append({
                                "id": f"chart_{page_idx}_{len(page_charts)}",
                                "title": chart_config.title or f"{chart_config.chart_type.upper()}: {chart_config.y_columns[0] if chart_config.y_columns else ''}",
                                "image": f"data:image/png;base64,{img_data}"
                            })
                            
                    except Exception as e:
                        print(f"❌ Error exporting chart: {e}")
                
                if page_charts:
                    pages_data.append({
                        "name": page.name,
                        "charts": page_charts
                    })
            
            html = self._generate_multi_page_html(pages_data)
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            
            import shutil
            shutil.rmtree(temp_dir)
            
            self.statusBar().showMessage(f"✅ Exported {len(pages_data)} pages to {path}", 3000)
            print(f"✅ Exported {len(pages_data)} pages to {path}")
            
        except Exception as e:
            print(f"❌ Error exporting: {e}")
            import traceback
            traceback.print_exc()
            self.statusBar().showMessage(f"Error exporting: {e}", 5000)

    def _generate_multi_page_html(self, pages_data: list) -> str:
        import json
        pages_json = json.dumps(pages_data)
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Export</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        
        .dashboard {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .dashboard-header {{
            padding-bottom: 20px;
            border-bottom: 2px solid #e8e8e8;
            margin-bottom: 20px;
        }}
        
        .dashboard-header h1 {{
            font-size: 28px;
            color: #333;
            font-weight: 300;
        }}
        
        .dashboard-header p {{
            color: #888;
            font-size: 14px;
            margin-top: 5px;
        }}
        
        .tabs {{
            display: flex;
            gap: 5px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e8e8e8;
            padding-bottom: 10px;
            flex-wrap: wrap;
        }}
        
        .tab-btn {{
            padding: 10px 20px;
            background: #f0f0f0;
            border: none;
            border-radius: 6px 6px 0 0;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            color: #666;
            transition: all 0.2s;
        }}
        
        .tab-btn:hover {{
            background: #e0e0e0;
        }}
        
        .tab-btn.active {{
            background: #0078d4;
            color: white;
        }}
        
        .page-content {{
            display: none;
            animation: fadeIn 0.3s ease;
        }}
        
        .page-content.active {{
            display: block;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
        }}
        
        .chart-container {{
            background: white;
            border: 1px solid #e8e8e8;
            border-radius: 8px;
            padding: 15px;
            transition: box-shadow 0.2s;
        }}
        
        .chart-container:hover {{
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        
        .chart-title {{
            font-size: 14px;
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
            text-align: center;
        }}
        
        .chart-wrapper {{
            width: 100%;
            overflow: hidden;
        }}
        
        .chart-image {{
            width: 100%;
            height: auto;
            display: block;
        }}
        
        .page-info {{
            text-align: center;
            color: #999;
            font-size: 13px;
            margin-bottom: 15px;
        }}
        
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e8e8e8;
            text-align: center;
            color: #999;
            font-size: 12px;
        }}
        
        .no-charts {{
            text-align: center;
            padding: 40px;
            color: #999;
            font-size: 16px;
        }}
        
        @media (max-width: 600px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
            
            .dashboard {{
                padding: 10px;
            }}
            
            .tab-btn {{
                padding: 8px 12px;
                font-size: 12px;
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="dashboard-header">
            <h1>📊 Dashboard Export</h1>
            <p>Generated on {pd.Timestamp.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <div class="tabs" id="tabs"></div>
        <div id="pages-container"></div>
        
        <div class="footer">
            Exported from BI Builder · All rights reserved
        </div>
    </div>

    <script>
        const pagesData = {pages_json};
        let currentPage = 0;
        
        function renderTabs() {{
            const tabsContainer = document.getElementById('tabs');
            tabsContainer.innerHTML = '';
            
            pagesData.forEach((page, index) => {{
                const btn = document.createElement('button');
                btn.className = 'tab-btn' + (index === currentPage ? ' active' : '');
                btn.textContent = page.name + ' (' + page.charts.length + ')';
                btn.onclick = () => switchPage(index);
                tabsContainer.appendChild(btn);
            }});
        }}
        
        function renderPages() {{
            const container = document.getElementById('pages-container');
            container.innerHTML = '';
            
            pagesData.forEach((page, index) => {{
                const pageDiv = document.createElement('div');
                pageDiv.className = 'page-content' + (index === currentPage ? ' active' : '');
                pageDiv.id = 'page-' + index;
                
                if (page.charts.length === 0) {{
                    pageDiv.innerHTML = '<div class="no-charts">No charts on this page</div>';
                }} else {{
                    let chartsHtml = '<div class="page-info">' + page.charts.length + ' chart(s)</div>';
                    chartsHtml += '<div class="charts-grid">';
                    
                    page.charts.forEach(chart => {{
                        chartsHtml += `
                            <div class="chart-container">
                                <div class="chart-title">${{chart.title}}</div>
                                <div class="chart-wrapper">
                                    <img src="${{chart.image}}" alt="${{chart.title}}" class="chart-image">
                                </div>
                            </div>
                        `;
                    }});
                    
                    chartsHtml += '</div>';
                    pageDiv.innerHTML = chartsHtml;
                }}
                
                container.appendChild(pageDiv);
            }});
        }}
        
        function switchPage(index) {{
            document.querySelectorAll('.page-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            
            const pageEl = document.getElementById('page-' + index);
            if (pageEl) pageEl.classList.add('active');
            
            const tabs = document.querySelectorAll('.tab-btn');
            if (tabs[index]) tabs[index].classList.add('active');
            
            currentPage = index;
        }}
        
        renderTabs();
        renderPages();
        switchPage(0);
    </script>
</body>
</html>
        """

    # =========================================================
    # EXPORT INTERACTIVE HTML
    # =========================================================

    def export_interactive_html(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Interactive HTML", "", "HTML (*.html)"
        )
        if not path:
            return
        
        try:
            dashboard = self.dashboard_manager.get_current_dashboard()
            
            total_charts = 0
            for page in dashboard.pages:
                total_charts += len(page.charts)
            
            if total_charts == 0:
                self.statusBar().showMessage("⚠️ No charts to export", 3000)
                return
            
            html = self._generate_interactive_html(dashboard)
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            
            self.statusBar().showMessage(f"✅ Interactive dashboard exported to {path}", 3000)
            print(f"✅ Interactive dashboard exported to {path}")
            
        except Exception as e:
            print(f"❌ Error exporting: {e}")
            import traceback
            traceback.print_exc()
            self.statusBar().showMessage(f"Error exporting: {e}", 5000)

    def _generate_interactive_html(self, dashboard) -> str:
        import plotly.graph_objects as go
        import json
        
        pages_data = []
        
        for page_idx, page in enumerate(dashboard.pages):
            page_charts = []
            
            for chart_config in page.charts:
                try:
                    if chart_config.chart_type in ["text", "shape", "map"]:
                        continue
                    
                    if chart_config.dataset_name not in self.datasets:
                        continue
                    
                    df = self.datasets[chart_config.dataset_name]
                    if chart_config.x_column not in df.columns:
                        continue
                    
                    valid_y_columns = [col for col in chart_config.y_columns if col in df.columns]
                    if not valid_y_columns:
                        continue
                    
                    fig = self._create_plotly_figure(
                        df, 
                        chart_config.chart_type,
                        chart_config.x_column,
                        valid_y_columns[0] if valid_y_columns else "",
                        chart_config.title or f"{chart_config.chart_type.upper()}: {valid_y_columns[0] if valid_y_columns else ''}",
                        chart_config.color
                    )
                    
                    fig_json = fig.to_json()
                    
                    page_charts.append({
                        "id": f"chart_{page_idx}_{len(page_charts)}",
                        "title": chart_config.title or f"{chart_config.chart_type.upper()}: {valid_y_columns[0] if valid_y_columns else ''}",
                        "fig_json": fig_json,
                        "x_column": chart_config.x_column,
                        "y_column": valid_y_columns[0] if valid_y_columns else "",
                        "chart_type": chart_config.chart_type
                    })
                    
                except Exception as e:
                    print(f"❌ Error creating chart for HTML: {e}")
            
            if page_charts:
                pages_data.append({
                    "name": page.name,
                    "charts": page_charts
                })
        
        return self._generate_interactive_html_template(pages_data)

    def _create_plotly_figure(self, df, chart_type, x_col, y_col, title, color):
        if chart_type == "line":
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode='lines+markers',
                name=y_col,
                line=dict(color=color)
            ))
        elif chart_type == "scatter":
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode='markers',
                name=y_col,
                marker=dict(color=color, size=8)
            ))
        elif chart_type == "bar":
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df[x_col],
                y=df[y_col],
                name=y_col,
                marker=dict(color=color)
            ))
        elif chart_type == "pie":
            fig = go.Figure()
            fig.add_trace(go.Pie(
                labels=df[x_col][:20],
                values=df[y_col][:20],
                name=y_col
            ))
        elif chart_type == "area":
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode='lines',
                name=y_col,
                fill='tozeroy',
                line=dict(color=color)
            ))
        elif chart_type == "donut":
            fig = go.Figure()
            fig.add_trace(go.Pie(
                labels=df[x_col][:20],
                values=df[y_col][:20],
                name=y_col,
                hole=0.4
            ))
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode='markers',
                name=y_col,
                marker=dict(color=color, size=8)
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_col,
            yaxis_title=y_col,
            template='plotly_white',
            hovermode='closest'
        )
        
        return fig

    def _generate_interactive_html_template(self, pages_data) -> str:
        import json
        pages_json = json.dumps(pages_data)
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Dashboard Export</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        
        .dashboard {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .dashboard-header {{
            padding-bottom: 20px;
            border-bottom: 2px solid #e8e8e8;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .dashboard-header h1 {{
            font-size: 28px;
            color: #333;
            font-weight: 300;
        }}
        
        .dashboard-header p {{
            color: #888;
            font-size: 14px;
        }}
        
        .controls {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f8f8;
            border-radius: 8px;
        }}
        
        .filter-group {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .filter-group label {{
            font-weight: 500;
            font-size: 13px;
            color: #555;
        }}
        
        .reset-btn {{
            padding: 5px 15px;
            background: #dc3545;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
        }}
        
        .reset-btn:hover {{
            background: #c82333;
        }}
        
        .tabs {{
            display: flex;
            gap: 5px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e8e8e8;
            padding-bottom: 10px;
            flex-wrap: wrap;
        }}
        
        .tab-btn {{
            padding: 10px 20px;
            background: #f0f0f0;
            border: none;
            border-radius: 6px 6px 0 0;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            color: #666;
            transition: all 0.2s;
        }}
        
        .tab-btn:hover {{
            background: #e0e0e0;
        }}
        
        .tab-btn.active {{
            background: #0078d4;
            color: white;
        }}
        
        .page-content {{
            display: none;
            animation: fadeIn 0.3s ease;
        }}
        
        .page-content.active {{
            display: block;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
        }}
        
        .chart-container {{
            background: white;
            border: 1px solid #e8e8e8;
            border-radius: 8px;
            padding: 15px;
            transition: box-shadow 0.2s;
        }}
        
        .chart-container:hover {{
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        
        .chart-title {{
            font-size: 14px;
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
            text-align: center;
        }}
        
        .chart-wrapper {{
            width: 100%;
        }}
        
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e8e8e8;
            text-align: center;
            color: #999;
            font-size: 12px;
        }}
        
        @media (max-width: 600px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
            
            .dashboard {{
                padding: 10px;
            }}
            
            .tab-btn {{
                padding: 8px 12px;
                font-size: 12px;
            }}
            
            .controls {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="dashboard-header">
            <div>
                <h1>📊 Interactive Dashboard</h1>
                <p>Click on any chart to filter others</p>
            </div>
            <div>
                <button class="reset-btn" onclick="resetAllFilters()">🔄 Reset Filters</button>
            </div>
        </div>
        
        <div class="controls" id="filters">
            <div class="filter-group">
                <label>📌 Filters:</label>
                <span style="color: #999; font-size: 13px;">Click on chart points to filter</span>
            </div>
        </div>
        
        <div class="tabs" id="tabs"></div>
        <div id="pages-container"></div>
        
        <div class="footer">
            Exported from BI Builder · All rights reserved
        </div>
    </div>

    <script>
        const pagesData = {pages_json};
        let currentPage = 0;
        let globalFilters = {{}};
        let chartsData = {{}};
        
        function renderTabs() {{
            const tabsContainer = document.getElementById('tabs');
            tabsContainer.innerHTML = '';
            
            pagesData.forEach((page, index) => {{
                const btn = document.createElement('button');
                btn.className = 'tab-btn' + (index === currentPage ? ' active' : '');
                btn.textContent = page.name + ' (' + page.charts.length + ' charts)';
                btn.onclick = () => switchPage(index);
                tabsContainer.appendChild(btn);
            }});
        }}
        
        function renderPages() {{
            const container = document.getElementById('pages-container');
            container.innerHTML = '';
            
            pagesData.forEach((page, index) => {{
                const pageDiv = document.createElement('div');
                pageDiv.className = 'page-content' + (index === currentPage ? ' active' : '');
                pageDiv.id = 'page-' + index;
                
                if (page.charts.length === 0) {{
                    pageDiv.innerHTML = '<div style="text-align:center;padding:40px;color:#999;">No charts on this page</div>';
                }} else {{
                    let chartsHtml = '<div class="charts-grid">';
                    
                    page.charts.forEach((chart) => {{
                        const chartId = chart.id;
                        chartsData[chartId] = chart;
                        
                        chartsHtml += `
                            <div class="chart-container">
                                <div class="chart-title">${{chart.title}}</div>
                                <div class="chart-wrapper" id="${{chartId}}"></div>
                            </div>
                        `;
                    }});
                    
                    chartsHtml += '</div>';
                    pageDiv.innerHTML = chartsHtml;
                }}
                
                container.appendChild(pageDiv);
            }});
        }}
        
        function renderCharts() {{
            pagesData.forEach((page) => {{
                page.charts.forEach((chart) => {{
                    const container = document.getElementById(chart.id);
                    if (!container) return;
                    
                    let figData = JSON.parse(chart.fig_json);
                    
                    Plotly.react(chart.id, figData.data, figData.layout, {{responsive: true}});
                    
                    document.getElementById(chart.id).on('plotly_click', function(data) {{
                        if (data.points && data.points.length > 0) {{
                            const point = data.points[0];
                            const xValue = point.x;
                            const xColumn = chart.x_column;
                            
                            globalFilters[xColumn] = xValue;
                            updateFiltersDisplay();
                            renderCharts();
                        }}
                    }});
                }});
            }});
        }}
        
        function updateFiltersDisplay() {{
            const container = document.getElementById('filters');
            let html = '<div class="filter-group"><label>📌 Filters:</label>';
            
            if (Object.keys(globalFilters).length === 0) {{
                html += '<span style="color: #999; font-size: 13px;">No active filters</span>';
            }} else {{
                Object.keys(globalFilters).forEach(key => {{
                    html += `<span style="background:#0078d4;color:white;padding:3px 10px;border-radius:12px;font-size:12px;margin:0 5px;">${{key}}: ${{globalFilters[key]}}</span>`;
                }});
            }}
            
            html += '</div>';
            container.innerHTML = html;
        }}
        
        function resetAllFilters() {{
            globalFilters = {{}};
            updateFiltersDisplay();
            renderCharts();
        }}
        
        function switchPage(index) {{
            document.querySelectorAll('.page-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            
            const pageEl = document.getElementById('page-' + index);
            if (pageEl) pageEl.classList.add('active');
            
            const tabs = document.querySelectorAll('.tab-btn');
            if (tabs[index]) tabs[index].classList.add('active');
            
            currentPage = index;
            
            setTimeout(() => {{
                renderCharts();
            }}, 100);
        }}
        
        renderTabs();
        renderPages();
        updateFiltersDisplay();
        switchPage(0);
    </script>
</body>
</html>
        """

    # =========================================================
    # UNDO/REDO
    # =========================================================

    def save_history_state(self):
        if not self.dashboard_manager.dashboards:
            return
        
        data = self.dashboard_manager.to_dict()
        self.history_manager.push_state(data)
        self._update_undo_buttons()

    def undo_action(self):
        if not self.history_manager.can_undo():
            return
        
        current_data = self.dashboard_manager.to_dict()
        previous_data = self.history_manager.undo(current_data)
        
        if previous_data:
            self._restore_state(previous_data)
            self._update_undo_buttons()
            self.statusBar().showMessage("↩️ Undo", 2000)

    def redo_action(self):
        if not self.history_manager.can_redo():
            return
        
        current_data = self.dashboard_manager.to_dict()
        next_data = self.history_manager.redo(current_data)
        
        if next_data:
            self._restore_state(next_data)
            self._update_undo_buttons()
            self.statusBar().showMessage("↪️ Redo", 2000)

    def _restore_state(self, data):
        self.dashboard_manager = DashboardManager.from_dict(data)
        
        names = self.dashboard_manager.get_dashboard_names()
        current = self.dashboard_manager.current_index
        self.tab_bar.set_tabs(names, current)
        
        dashboard = self.dashboard_manager.get_current_dashboard()
        self.page_tab_bar.set_pages(dashboard.get_page_names(), dashboard.current_page)
        
        self.load_dashboard(current)

    def _update_undo_buttons(self):
        if hasattr(self, 'undo_btn'):
            self.undo_btn.setEnabled(self.history_manager.can_undo())
        if hasattr(self, 'redo_btn'):
            self.redo_btn.setEnabled(self.history_manager.can_redo())

    # =========================================================
    # PROJECT SAVE/LOAD
    # =========================================================

    def save_project(self):
        if not self.project_path:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save project", "", "JSON (*.json)"
            )
            if not path:
                return
            self.project_path = path
        
        try:
            import json
            
            datasets_json = {}
            for name, df in self.datasets.items():
                try:
                    datasets_json[name] = df.to_json(orient="split")
                except Exception as e:
                    print(f"❌ Error serializing dataset {name}: {e}")
            
            self.save_current_dashboard()
            
            data = {
                "version": "1.0",
                "datasets": datasets_json,
                "dashboard_manager": self.dashboard_manager.to_dict()
            }
            
            with open(self.project_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            self.statusBar().showMessage(f"✅ Project saved to {self.project_path}", 3000)
            print(f"✅ Project saved to {self.project_path} ({len(datasets_json)} datasets)")
            
        except Exception as e:
            print(f"❌ Error saving project: {e}")
            self.statusBar().showMessage(f"Error saving project: {e}", 5000)

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load project", "", "JSON (*.json)"
        )
        if not path:
            return
        
        try:
            import json
            
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.project_path = path
            
            if "datasets" in data:
                for name, df_json in data["datasets"].items():
                    try:
                        df = pd.read_json(df_json, orient="split")
                        self.datasets[name] = df
                        self.dataset_selector.addItem(name)
                        print(f"✅ Restored dataset: {name} ({len(df)} rows)")
                    except Exception as e:
                        print(f"❌ Error restoring dataset {name}: {e}")
            
            if self.datasets:
                first_dataset = list(self.datasets.keys())[0]
                self.dataset_selector.setCurrentText(first_dataset)
                self.set_dataset(first_dataset)
            
            if "dashboard_manager" in data:
                self.dashboard_manager = DashboardManager.from_dict(
                    data["dashboard_manager"]
                )
            
            names = self.dashboard_manager.get_dashboard_names()
            current = self.dashboard_manager.current_index
            self.tab_bar.set_tabs(names, current)
            
            self.load_dashboard(current)
            self.save_history_state()
            
            self.statusBar().showMessage(f"✅ Project loaded from {path}", 3000)
            print(f"✅ Project loaded from {path}")
            
        except Exception as e:
            print(f"❌ Error loading project: {e}")
            self.statusBar().showMessage(f"Error loading project: {e}", 5000)

    # =========================================================
    # EVENT HANDLING
    # =========================================================

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        
        selected = self.canvas.scene.selectedItems()
        if selected and (isinstance(selected[0], PlotItem) or isinstance(selected[0], MapItem)):
            self.update_selection_info(selected[0])
        else:
            self.properties_panel.current_item = None
            self.properties_panel.set_columns([])
            self.properties_panel.set_properties({
                "y_columns": [],
                "aggregation": "none",
                "title": "",
                "color": "#0078d4",
                "show_legend": True,
                "width": 600,
                "height": 350
            })