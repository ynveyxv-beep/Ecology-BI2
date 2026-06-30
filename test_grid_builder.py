# test_grid_builder.py - Стиль Яндекс DataLens (чистый)
import sys
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGridLayout, QFrame, QDialog,
    QListWidget, QListWidgetItem, QStackedWidget,
    QComboBox, QSpinBox, QLineEdit, QSlider,
    QTextEdit, QColorDialog, QSplitter, QTabWidget,
    QFileDialog, QFormLayout
)
from PySide6.QtGui import QColor


class WidgetCreationDialog(QDialog):
    widget_created = Signal(str, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новый виджет")
        self.setMinimumSize(750, 520)
        self.setModal(True)
        self.current_widget_type = None
        self.init_ui()
        self.create_default_preview()
    
    def init_ui(self):
        main = QHBoxLayout(self)
        main.setSpacing(0)
        main.setContentsMargins(0, 0, 0, 0)
        
        # ─── Левая панель ──────────────────────────────────────────────────
        left = QWidget()
        left.setFixedWidth(120)
        left.setStyleSheet("background: #f5f6f8;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(6, 10, 6, 10)
        left_layout.setSpacing(2)
        
        self.widget_list = QListWidget()
        self.widget_list.setStyleSheet("""
            QListWidget { border: none; background: transparent; }
            QListWidget::item { padding: 5px 6px; border-radius: 3px; font-size: 12px; }
            QListWidget::item:hover { background: #e8eaed; }
            QListWidget::item:selected { background: #1F4E79; color: white; }
        """)
        
        for name, wtype in [
            ("KPI", "kpi"),
            ("График", "chart"),
            ("Таблица", "table"),
            ("Текст", "text"),
            ("Изображение", "image"),
            ("Карта", "map"),
        ]:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, wtype)
            self.widget_list.addItem(item)
        
        self.widget_list.currentItemChanged.connect(self.on_widget_selected)
        left_layout.addWidget(self.widget_list)
        left_layout.addStretch()
        
        btn = QPushButton("Создать")
        btn.setStyleSheet("""
            QPushButton {
                background: #1F4E79;
                color: white;
                padding: 4px 0;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background: #2a6b9e; }
        """)
        btn.clicked.connect(self.create_widget)
        left_layout.addWidget(btn)
        
        # ─── Правая панель ─────────────────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(12, 10, 12, 10)
        right_layout.setSpacing(8)
        
        # Превью (просто белая область, без заголовка)
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(140)
        self.preview_label.setStyleSheet("""
            QLabel {
                background: white;
                border: 1px solid #e8eaed;
                border-radius: 4px;
            }
        """)
        right_layout.addWidget(self.preview_label)
        
        # Настройки (просто поля, без заголовка и рамок)
        self.settings_stack = QStackedWidget()
        self.settings_stack.setStyleSheet("background: #f5f6f8; border-radius: 4px;")
        right_layout.addWidget(self.settings_stack)
        
        default_page = QLabel("Выберите тип")
        default_page.setAlignment(Qt.AlignCenter)
        default_page.setStyleSheet("color: #bbb; font-size: 13px;")
        self.settings_stack.addWidget(default_page)
        
        self.settings_stack.addWidget(self._create_kpi_settings())
        self.settings_stack.addWidget(self._create_chart_settings())
        self.settings_stack.addWidget(self._create_table_settings())
        self.settings_stack.addWidget(self._create_text_settings())
        self.settings_stack.addWidget(self._create_image_settings())
        self.settings_stack.addWidget(self._create_map_settings())
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([120, 630])
        main.addWidget(splitter)
    
    def _create_kpi_settings(self):
        w = QWidget()
        layout = QFormLayout(w)
        layout.setSpacing(3)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setLabelAlignment(Qt.AlignRight)
        
        self.kpi_title = QLineEdit()
        self.kpi_title.setPlaceholderText("Название")
        self.kpi_title.textChanged.connect(self.update_preview)
        layout.addRow("Название", self.kpi_title)
        
        self.kpi_value = QLineEdit()
        self.kpi_value.setPlaceholderText("Значение")
        self.kpi_value.textChanged.connect(self.update_preview)
        layout.addRow("Значение", self.kpi_value)
        
        cw = QWidget()
        cl = QHBoxLayout(cw)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(4)
        self.kpi_color_preview = QLabel("  ")
        self.kpi_color_preview.setFixedSize(22, 18)
        self.kpi_color_preview.setStyleSheet("background: #1F4E79; border: 1px solid #ccc; border-radius: 2px;")
        cl.addWidget(self.kpi_color_preview)
        cb = QPushButton("...")
        cb.setFixedWidth(22)
        cb.clicked.connect(lambda: self._pick_color('kpi'))
        cl.addWidget(cb)
        cl.addStretch()
        layout.addRow("Цвет", cw)
        
        self.kpi_font = QSpinBox()
        self.kpi_font.setRange(12, 48)
        self.kpi_font.setValue(24)
        self.kpi_font.valueChanged.connect(self.update_preview)
        layout.addRow("Размер", self.kpi_font)
        
        return w
    
    def _create_chart_settings(self):
        w = QWidget()
        layout = QFormLayout(w)
        layout.setSpacing(3)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setLabelAlignment(Qt.AlignRight)
        
        self.chart_type = QComboBox()
        self.chart_type.addItems(["Линия", "Столбцы", "Точки"])
        self.chart_type.currentTextChanged.connect(self.update_preview)
        layout.addRow("Тип", self.chart_type)
        
        self.chart_title = QLineEdit()
        self.chart_title.setPlaceholderText("Заголовок")
        self.chart_title.textChanged.connect(self.update_preview)
        layout.addRow("Заголовок", self.chart_title)
        
        cw = QWidget()
        cl = QHBoxLayout(cw)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(4)
        self.chart_color_preview = QLabel("  ")
        self.chart_color_preview.setFixedSize(22, 18)
        self.chart_color_preview.setStyleSheet("background: #1F4E79; border: 1px solid #ccc; border-radius: 2px;")
        cl.addWidget(self.chart_color_preview)
        cb = QPushButton("...")
        cb.setFixedWidth(22)
        cb.clicked.connect(lambda: self._pick_color('chart'))
        cl.addWidget(cb)
        cl.addStretch()
        layout.addRow("Цвет", cw)
        
        self.chart_width = QSpinBox()
        self.chart_width.setRange(1, 5)
        self.chart_width.setValue(2)
        self.chart_width.valueChanged.connect(self.update_preview)
        layout.addRow("Толщина", self.chart_width)
        
        return w
    
    def _create_table_settings(self):
        w = QWidget()
        layout = QFormLayout(w)
        layout.setSpacing(3)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setLabelAlignment(Qt.AlignRight)
        
        self.table_title = QLineEdit()
        self.table_title.setPlaceholderText("Название")
        self.table_title.textChanged.connect(self.update_preview)
        layout.addRow("Название", self.table_title)
        
        self.table_limit = QSpinBox()
        self.table_limit.setRange(0, 1000)
        self.table_limit.setValue(100)
        self.table_limit.valueChanged.connect(self.update_preview)
        layout.addRow("Лимит", self.table_limit)
        
        return w
    
    def _create_text_settings(self):
        w = QWidget()
        layout = QFormLayout(w)
        layout.setSpacing(3)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setLabelAlignment(Qt.AlignRight)
        
        self.text_content = QTextEdit()
        self.text_content.setPlaceholderText("Текст...")
        self.text_content.setMaximumHeight(44)
        self.text_content.textChanged.connect(self.update_preview)
        layout.addRow("Текст", self.text_content)
        
        self.text_font = QSpinBox()
        self.text_font.setRange(8, 36)
        self.text_font.setValue(14)
        self.text_font.valueChanged.connect(self.update_preview)
        layout.addRow("Размер", self.text_font)
        
        return w
    
    def _create_image_settings(self):
        w = QWidget()
        layout = QFormLayout(w)
        layout.setSpacing(3)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setLabelAlignment(Qt.AlignRight)
        
        pw = QWidget()
        pl = QHBoxLayout(pw)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(3)
        self.image_path = QLineEdit()
        self.image_path.setPlaceholderText("Путь...")
        self.image_path.textChanged.connect(self.update_preview)
        pl.addWidget(self.image_path)
        cb = QPushButton("...")
        cb.setFixedWidth(22)
        cb.clicked.connect(self._browse_image)
        pl.addWidget(cb)
        layout.addRow("Файл", pw)
        
        self.image_scale = QSlider(Qt.Horizontal)
        self.image_scale.setRange(10, 200)
        self.image_scale.setValue(100)
        self.image_scale.valueChanged.connect(self.update_preview)
        layout.addRow("Масштаб", self.image_scale)
        
        return w
    
    def _create_map_settings(self):
        w = QWidget()
        layout = QFormLayout(w)
        layout.setSpacing(3)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setLabelAlignment(Qt.AlignRight)
        
        self.map_type = QComboBox()
        self.map_type.addItems(["Тепловая", "Точечная", "Полигоны"])
        self.map_type.currentTextChanged.connect(self.update_preview)
        layout.addRow("Тип", self.map_type)
        
        self.map_field = QComboBox()
        self.map_field.addItems(["omsu", "mro", "region"])
        self.map_field.currentTextChanged.connect(self.update_preview)
        layout.addRow("Поле", self.map_field)
        
        return w
    
    def _pick_color(self, target):
        c = QColorDialog.getColor()
        if c.isValid():
            h = c.name()
            if target == 'kpi':
                self.kpi_color_preview.setStyleSheet(f"background: {h}; border: 1px solid #ccc; border-radius: 2px;")
                self._kpi_color = h
            else:
                self.chart_color_preview.setStyleSheet(f"background: {h}; border: 1px solid #ccc; border-radius: 2px;")
                self._chart_color = h
            self.update_preview()
    
    def _browse_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if path:
            self.image_path.setText(path)
    
    def on_widget_selected(self, current, previous):
        if not current:
            return
        self.current_widget_type = current.data(Qt.UserRole)
        idx = {'kpi':1, 'chart':2, 'table':3, 'text':4, 'image':5, 'map':6}.get(self.current_widget_type, 0)
        self.settings_stack.setCurrentIndex(idx)
        self.update_preview()
    
    def create_default_preview(self):
        self.preview_label.setText("Выберите тип")
        self.preview_label.setStyleSheet("""
            QLabel {
                background: white;
                border: 1px solid #e8eaed;
                border-radius: 4px;
                color: #bbb;
                font-size: 13px;
            }
        """)
    
    def update_preview(self):
        if not self.current_widget_type:
            return
        getattr(self, f'_update_{self.current_widget_type}_preview', lambda: None)()
    
    def _update_kpi_preview(self):
        t = self.kpi_title.text() or "KPI"
        v = self.kpi_value.text() or "—"
        c = getattr(self, '_kpi_color', '#1F4E79')
        s = self.kpi_font.value()
        self.preview_label.setText(f"""
        <div style="text-align:center; padding:16px;">
            <div style="font-size:{s}px; font-weight:bold; color:{c};">{v}</div>
            <div style="font-size:12px; color:#999; margin-top:3px;">{t}</div>
        </div>
        """)
        self.preview_label.setStyleSheet("background: white; border: 1px solid #e8eaed; border-radius: 4px;")
    
    def _update_chart_preview(self):
        t = self.chart_title.text() or "График"
        c = getattr(self, '_chart_color', '#1F4E79')
        self.preview_label.setText(f"""
        <div style="padding:12px; text-align:center;">
            <div style="font-weight:bold; font-size:12px; margin-bottom:6px;">{t}</div>
            <div style="background:#f5f6f8; border-radius:3px; padding:12px;">
                <svg width="100%" height="70" viewBox="0 0 260 70">
                    <line x1="12" y1="60" x2="12" y2="8" stroke="#ddd" stroke-width="1"/>
                    <line x1="12" y1="60" x2="248" y2="60" stroke="#ddd" stroke-width="1"/>
                    <polyline points="12,52 52,30 92,48 132,18 172,35 212,14" fill="none" stroke="{c}" stroke-width="2.5"/>
                    <circle cx="12" cy="52" r="3" fill="{c}"/>
                    <circle cx="52" cy="30" r="3" fill="{c}"/>
                    <circle cx="92" cy="48" r="3" fill="{c}"/>
                    <circle cx="132" cy="18" r="3" fill="{c}"/>
                    <circle cx="172" cy="35" r="3" fill="{c}"/>
                    <circle cx="212" cy="14" r="3" fill="{c}"/>
                </svg>
            </div>
        </div>
        """)
        self.preview_label.setStyleSheet("background: white; border: 1px solid #e8eaed; border-radius: 4px;")
    
    def _update_table_preview(self):
        t = self.table_title.text() or "Таблица"
        l = self.table_limit.value()
        self.preview_label.setText(f"""
        <div style="padding:12px;">
            <div style="font-weight:bold; font-size:12px; margin-bottom:4px;">{t}</div>
            <div style="background:#f8f9fa; border-radius:3px; padding:8px; text-align:center; color:#999; font-size:12px;">
                📋 {l} строк
            </div>
        </div>
        """)
        self.preview_label.setStyleSheet("background: white; border: 1px solid #e8eaed; border-radius: 4px;")
    
    def _update_text_preview(self):
        content = self.text_content.toPlainText() or "Текст"
        s = self.text_font.value()
        self.preview_label.setText(f"""
        <div style="padding:16px; text-align:center;">
            <div style="font-size:{s}px; color:#333;">{content}</div>
        </div>
        """)
        self.preview_label.setStyleSheet("background: white; border: 1px solid #e8eaed; border-radius: 4px;")
    
    def _update_image_preview(self):
        path = self.image_path.text()
        scale = self.image_scale.value()
        if path:
            name = path.split('/')[-1]
            self.preview_label.setText(f"""
            <div style="padding:14px; text-align:center;">
                <div style="font-size:36px;">🖼️</div>
                <div style="font-size:12px; color:#1F4E79; margin-top:4px;">{name}</div>
                <div style="font-size:10px; color:#999;">{scale}%</div>
            </div>
            """)
        else:
            self.preview_label.setText("""
            <div style="padding:20px; text-align:center; color:#bbb;">
                <div style="font-size:36px;">🖼️</div>
                <div style="font-size:12px; margin-top:4px;">Выберите изображение</div>
            </div>
            """)
        self.preview_label.setStyleSheet("background: white; border: 1px solid #e8eaed; border-radius: 4px;")
    
    def _update_map_preview(self):
        mt = self.map_type.currentText()
        mf = self.map_field.currentText()
        self.preview_label.setText(f"""
        <div style="padding:14px; text-align:center;">
            <div style="font-size:36px;">🗺️</div>
            <div style="font-size:13px; font-weight:bold; color:#1F4E79; margin-top:4px;">{mt}</div>
            <div style="font-size:11px; color:#999;">{mf}</div>
            <div style="background:#f5f6f8; border-radius:3px; padding:6px; margin-top:4px; font-size:10px; color:#999;">
                ● ● ● ● ●
            </div>
        </div>
        """)
        self.preview_label.setStyleSheet("background: white; border: 1px solid #e8eaed; border-radius: 4px;")
    
    def create_widget(self):
        if not self.current_widget_type:
            return
        t = self.current_widget_type
        settings = {}
        if t == 'kpi':
            settings = {'title': self.kpi_title.text(), 'value': self.kpi_value.text(), 'color': getattr(self, '_kpi_color', '#1F4E79'), 'font_size': self.kpi_font.value()}
        elif t == 'chart':
            settings = {'type': self.chart_type.currentText(), 'title': self.chart_title.text(), 'color': getattr(self, '_chart_color', '#1F4E79'), 'line_width': self.chart_width.value()}
        elif t == 'table':
            settings = {'title': self.table_title.text(), 'limit': self.table_limit.value()}
        elif t == 'text':
            settings = {'content': self.text_content.toPlainText(), 'font_size': self.text_font.value()}
        elif t == 'image':
            settings = {'path': self.image_path.text(), 'scale': self.image_scale.value()}
        elif t == 'map':
            settings = {'type': self.map_type.currentText(), 'coord_field': self.map_field.currentText()}
        self.widget_created.emit(t, settings)
        self.accept()


# ─── ЯЧЕЙКА ───────────────────────────────────────────────────────────────

class PlusButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("+", parent)
        self.setFixedSize(44, 44)
        self.setStyleSheet("""
            QPushButton {
                background: #1F4E79;
                color: white;
                border: none;
                border-radius: 22px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover { background: #2a6b9e; }
        """)
        self.setCursor(Qt.PointingHandCursor)


class GridCell(QFrame):
    widget_added = Signal(str, dict)
    
    def __init__(self, row, col, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 6px;
                min-height: 110px;
                min-width: 110px;
            }
            QFrame:hover { border-color: #1F4E79; background: #e9ecef; }
        """)
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignCenter)
        self.plus = PlusButton(self)
        self.plus.clicked.connect(self.show_dialog)
        self.layout().addWidget(self.plus)
    
    def show_dialog(self):
        dlg = WidgetCreationDialog(self)
        dlg.widget_created.connect(self.add_widget)
        dlg.exec()
    
    def add_widget(self, wtype, settings):
        self.plus.deleteLater()
        content = self._create_content(wtype, settings)
        self.layout().addWidget(content)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 2px solid #1F4E79;
                border-radius: 6px;
            }
        """)
        self.widget_added.emit(wtype, settings)
    
    def _create_content(self, wtype, settings):
        if wtype == "kpi":
            w = QWidget()
            l = QVBoxLayout(w)
            l.setAlignment(Qt.AlignCenter)
            v = QLabel(settings.get('value', '—'))
            v.setStyleSheet(f"font-size:{settings.get('font_size', 24)}px; font-weight:bold; color:{settings.get('color', '#1F4E79')};")
            v.setAlignment(Qt.AlignCenter)
            l.addWidget(v)
            t = QLabel(settings.get('title', 'KPI'))
            t.setStyleSheet("color:#999; font-size:11px;")
            t.setAlignment(Qt.AlignCenter)
            l.addWidget(t)
            return w
        elif wtype == "chart":
            l = QLabel(f"📈 {settings.get('title', 'График')}")
            l.setStyleSheet(f"font-size:12px; color:{settings.get('color', '#1F4E79')}; background:#f5f6f8; padding:8px; border-radius:3px;")
            l.setAlignment(Qt.AlignCenter)
            return l
        elif wtype == "table":
            l = QLabel(f"📋 {settings.get('title', 'Таблица')}")
            l.setStyleSheet("font-size:12px; color:#1F4E79; background:#f5f6f8; padding:8px; border-radius:3px;")
            l.setAlignment(Qt.AlignCenter)
            return l
        elif wtype == "text":
            l = QLabel(settings.get('content', 'Текст'))
            l.setStyleSheet(f"font-size:{settings.get('font_size', 14)}px; color:#333;")
            l.setAlignment(Qt.AlignCenter)
            l.setWordWrap(True)
            return l
        elif wtype == "image":
            path = settings.get('path', '')
            l = QLabel(f"🖼️\n{path.split('/')[-1] if path else 'Изображение'}")
            l.setStyleSheet("font-size:11px; color:#1F4E79; background:#f5f6f8; padding:8px; border-radius:3px;")
            l.setAlignment(Qt.AlignCenter)
            return l
        elif wtype == "map":
            l = QLabel(f"🗺️\n{settings.get('type', 'Карта')}")
            l.setStyleSheet("font-size:12px; color:#1F4E79; background:#f5f6f8; padding:8px; border-radius:3px;")
            l.setAlignment(Qt.AlignCenter)
            return l
        return QLabel("?")


# ─── КОНСТРУКТОР ──────────────────────────────────────────────────────────

class GridBuilder(QWidget):
    def __init__(self):
        super().__init__()
        self.rows, self.cols = 2, 3
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        header = QHBoxLayout()
        header.addWidget(QLabel("Конструктор"))
        header.addStretch()
        for text, cb in [("+ Ряд", self.add_row), ("+ Колонка", self.add_col)]:
            btn = QPushButton(text)
            btn.setStyleSheet("padding:2px 8px; font-size:11px;")
            btn.clicked.connect(cb)
            header.addWidget(btn)
        layout.addLayout(header)
        
        self.grid = QGridLayout()
        self.grid.setSpacing(6)
        layout.addLayout(self.grid)
        self._build()
    
    def _build(self):
        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if w: w.deleteLater()
        
        for r in range(self.rows):
            for c in range(self.cols):
                cell = GridCell(r, c)
                cell.widget_added.connect(lambda wt, s, rr=r, cc=c: self.on_added(rr, cc, wt, s))
                self.grid.addWidget(cell, r, c)
        
        for i in range(self.rows):
            self.grid.setRowStretch(i, 1)
        for j in range(self.cols):
            self.grid.setColumnStretch(j, 1)
    
    def add_row(self):
        self.rows += 1
        self._build()
    
    def add_col(self):
        self.cols += 1
        self._build()
    
    def on_added(self, r, c, wt, s):
        print(f"✅ {wt} в ({r}, {c})")


# ─── ГЛАВНОЕ ОКНО ─────────────────────────────────────────────────────────

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Конструктор")
        self.setMinimumSize(850, 580)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        tab1 = QWidget()
        l1 = QVBoxLayout(tab1)
        l1.addWidget(GridBuilder())
        tabs.addTab(tab1, "Конструктор")
        
        tab2 = QWidget()
        l2 = QVBoxLayout(tab2)
        l2.addWidget(QLabel("Превью", alignment=Qt.AlignCenter))
        tabs.addTab(tab2, "Превью")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())