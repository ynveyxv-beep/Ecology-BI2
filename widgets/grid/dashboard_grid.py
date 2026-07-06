# widgets/grid/dashboard_grid.py
"""
Сетка конструктора на основе QSplitter:
- Строки — вертикальный QSplitter
- Ячейки в строке — горизонтальный QSplitter
- Пользователь тянет разделители мышью, виджеты тянутся
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QSplitter, QPushButton, QHBoxLayout, QVBoxLayout,
    QLabel, QScrollArea, QFrame
)

from widgets.grid.dashboard_cell import DashboardCell
from ui.theme import BG_DARK, BG_PANEL, BG_HOVER, BORDER, BORDER_LT, ACCENT, TEXT_SEC, TEXT_MUT


_SPLITTER_STYLE = f"""
    QSplitter::handle {{
        background: transparent;
        border-radius: 2px;
    }}
    QSplitter::handle:hover {{
        background: {ACCENT};
        opacity: 0.6;
    }}
    QSplitter::handle:pressed {{
        background: {ACCENT};
    }}
    QSplitter::handle:horizontal {{
        width: 3px;
        margin: 6px 0;
    }}
    QSplitter::handle:vertical {{
        height: 3px;
        margin: 0 6px;
    }}
"""


class DashboardGrid(QWidget):
    """
    Сетка конструктора дашбордов (QSplitter).

    Сигналы:
    - widget_added(row, col, widget_type, settings)
    - widget_removed(row, col)
    - grid_changed()
    """

    widget_added   = Signal(int, int, str, dict)
    widget_removed = Signal(int, int)
    grid_changed   = Signal()

    def __init__(self, rows: int = 2, cols: int = 3, parent=None):
        super().__init__(parent)
        self._rows = rows
        self._cols = cols
        self._cells = []           # list[list[DashboardCell]]
        self._row_splitters = []   # list[QSplitter]
        self._cell_widgets = {}    # (row, col) → BaseDashboardWidget
        self._widget_counter = 0
        self._df = None
        self._datasets: dict = {}

        self._init_ui()
        self._build_initial_grid()

    # ─── Свойства ──────────────────────────────────────────────────────────

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def cols(self) -> int:
        return self._cols

    @property
    def cells(self) -> list:
        return self._cells

    def cell_at(self, row: int, col: int) -> DashboardCell:
        if 0 <= row < self._rows and 0 <= col < self._cols:
            return self._cells[row][col]
        return None

    def widget_at(self, row: int, col: int) -> QWidget:
        cell = self.cell_at(row, col)
        return cell.widget if cell else None

    def is_empty_at(self, row: int, col: int) -> bool:
        cell = self.cell_at(row, col)
        return cell.is_empty if cell else True

    # ─── Публичные методы ──────────────────────────────────────────────────

    def add_row(self) -> None:
        """Добавляет новый ряд внизу."""
        row = self._rows
        self._rows += 1
        row_cells = []
        row_spl = self._make_row_splitter()
        for col in range(self._cols):
            cell = self._create_cell(row, col)
            cell.set_datasets(self._datasets)
            row_spl.addWidget(cell)
            row_cells.append(cell)
        self._cells.append(row_cells)
        self._row_splitters.append(row_spl)
        self._outer_splitter.addWidget(row_spl)
        row_spl.setSizes([1000] * self._cols)
        # Уравниваем высоты всех рядов
        self._outer_splitter.setSizes([1000] * self._rows)
        self.grid_changed.emit()

    def add_column(self) -> None:
        """Добавляет новую колонку справа во всех рядах."""
        col = self._cols
        self._cols += 1
        for row, row_spl in enumerate(self._row_splitters):
            cell = self._create_cell(row, col)
            cell.set_datasets(self._datasets)
            row_spl.addWidget(cell)
            self._cells[row].append(cell)
            row_spl.setSizes([1000] * self._cols)
        self.grid_changed.emit()

    def add_widget(self, widget: QWidget, widget_type: str, row: int, col: int,
                   row_span: int = 1, col_span: int = 1) -> bool:
        """Добавляет виджет в указанную ячейку."""
        cell = self.cell_at(row, col)
        if not cell or not cell.is_empty:
            return False
        cell.set_widget(widget, widget_type)
        self._cell_widgets[(row, col)] = widget
        if self._datasets and hasattr(widget, 'set_datasets'):
            widget.set_datasets(self._datasets)
        elif self._df is not None and hasattr(widget, 'set_data'):
            widget.set_data(self._df)
        self.widget_added.emit(row, col, widget_type, {})
        self.grid_changed.emit()
        return True

    def remove_widget(self, row: int, col: int) -> bool:
        """Удаляет виджет из ячейки."""
        cell = self.cell_at(row, col)
        if not cell or cell.is_empty:
            return False
        cell.clear()
        self._cell_widgets.pop((row, col), None)
        self.widget_removed.emit(row, col)
        self.grid_changed.emit()
        return True

    def clear(self) -> None:
        """Очищает все ячейки."""
        for row in range(self._rows):
            for col in range(self._cols):
                self.remove_widget(row, col)

    def get_widgets_count(self) -> int:
        return len(self._cell_widgets)

    def set_data(self, df) -> None:
        """Передаёт DataFrame во все виджеты сетки (устаревший метод)."""
        self._df = df
        for widget in self._cell_widgets.values():
            if hasattr(widget, 'set_data'):
                widget.set_data(df)

    def set_datasets(self, datasets: dict) -> None:
        """Передаёт все датасеты во все виджеты и ячейки сетки."""
        self._datasets = datasets
        # Виджеты
        for widget in self._cell_widgets.values():
            if hasattr(widget, 'set_datasets'):
                widget.set_datasets(datasets)
        # Ячейки (чтобы диалог создания знал о датасетах)
        for row in self._cells:
            for cell in row:
                cell.set_datasets(datasets)

    def serialize(self) -> dict:
        widgets = []
        counter = 0
        for (row, col), widget in self._cell_widgets.items():
            cell = self.cell_at(row, col)
            if cell and hasattr(widget, 'serialize'):
                counter += 1
                widgets.append({
                    'id':       f"widget_{counter}",
                    'type':     cell.widget_type,
                    'row':      row,
                    'col':      col,
                    'row_span': 1,
                    'col_span': 1,
                    'settings': widget.serialize(),
                })

        # Сохраняем пропорции строк (высоты)
        row_sizes = list(self._outer_splitter.sizes()) if hasattr(self, '_outer_splitter') else []

        # Сохраняем пропорции столбцов (средние по всем строкам)
        col_sizes_all = [list(spl.sizes()) for spl in self._row_splitters if spl.sizes()]
        if col_sizes_all:
            col_sizes = [
                sum(row[c] for row in col_sizes_all if c < len(row)) / len(col_sizes_all)
                for c in range(self._cols)
            ]
        else:
            col_sizes = [1000] * self._cols

        return {
            'version':   '1.0',
            'rows':      self._rows,
            'columns':   self._cols,
            'widgets':   widgets,
            'row_sizes': row_sizes,
            'col_sizes': col_sizes,
        }

    # ─── Приватные методы ──────────────────────────────────────────────────

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Прокручиваемый холст
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        canvas = QWidget()
        canvas.setStyleSheet(f"background:{BG_DARK};")
        self._canvas = canvas
        canvas_layout = QVBoxLayout(canvas)
        canvas_layout.setContentsMargins(16, 16, 16, 16)
        canvas_layout.setSpacing(0)

        # Вертикальный сплиттер — ряды
        self._outer_splitter = QSplitter(Qt.Vertical)
        self._outer_splitter.setChildrenCollapsible(False)
        self._outer_splitter.setHandleWidth(3)
        self._outer_splitter.setStyleSheet(_SPLITTER_STYLE)

        canvas_layout.addWidget(self._outer_splitter)
        canvas_layout.addStretch()

        scroll.setWidget(canvas)
        outer.addWidget(scroll, 1)

        # Нижняя панель
        bottom_bar = QWidget()
        bottom_bar.setStyleSheet(
            f"background:{BG_PANEL}; border-top:1px solid {BORDER};"
        )
        self._bottom_bar = bottom_bar
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(16, 6, 16, 6)
        bottom_layout.setSpacing(8)

        btn_style = f"""
            QPushButton {{
                background:{BG_DARK}; border:1px solid {BORDER};
                border-radius:4px; padding:4px 14px;
                font-size:12px; color:{TEXT_SEC};
            }}
            QPushButton:hover {{ background:{BG_HOVER}; border-color:{BORDER_LT}; color:{ACCENT}; }}
        """
        self._grid_btns = []
        for label, slot in [("+ Строка", self.add_row), ("+ Колонка", self.add_column)]:
            btn = QPushButton(label)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(slot)
            bottom_layout.addWidget(btn)
            self._grid_btns.append(btn)

        bottom_layout.addStretch()
        outer.addWidget(bottom_bar)

    def refresh_theme(self) -> None:
        """Перегенерирует все inline-стили из текущей темы."""
        import ui.theme as tm
        splitter_style = f"""
            QSplitter::handle {{
                background: transparent;
                border-radius: 2px;
            }}
            QSplitter::handle:hover {{
                background: {tm.ACCENT};
                opacity: 0.6;
            }}
            QSplitter::handle:pressed {{
                background: {tm.ACCENT};
            }}
            QSplitter::handle:horizontal {{
                width: 3px;
                margin: 6px 0;
            }}
            QSplitter::handle:vertical {{
                height: 3px;
                margin: 0 6px;
            }}
        """
        # Canvas background
        self._canvas.setStyleSheet(f"background:{tm.BG_DARK};")
        # Splitters
        self._outer_splitter.setStyleSheet(splitter_style)
        for spl in self._row_splitters:
            spl.setStyleSheet(splitter_style)
        # Bottom bar
        self._bottom_bar.setStyleSheet(
            f"background:{tm.BG_PANEL}; border-top:1px solid {tm.BORDER};"
        )
        btn_style = f"""
            QPushButton {{
                background:{tm.BG_DARK}; border:1px solid {tm.BORDER};
                border-radius:4px; padding:4px 14px;
                font-size:12px; color:{tm.TEXT_SEC};
            }}
            QPushButton:hover {{ background:{tm.BG_HOVER}; border-color:{tm.BORDER_LT}; color:{tm.ACCENT}; }}
        """
        for btn in self._grid_btns:
            btn.setStyleSheet(btn_style)
        # All cells
        for row_cells in self._cells:
            for cell in row_cells:
                cell.refresh_theme()

    def _make_row_splitter(self) -> QSplitter:
        spl = QSplitter(Qt.Horizontal)
        spl.setChildrenCollapsible(False)
        spl.setHandleWidth(3)
        spl.setStyleSheet(_SPLITTER_STYLE)
        spl.setMinimumHeight(160)
        return spl

    def _build_initial_grid(self):
        for row in range(self._rows):
            row_spl = self._make_row_splitter()
            row_cells = []
            for col in range(self._cols):
                cell = self._create_cell(row, col)
                row_spl.addWidget(cell)
                row_cells.append(cell)
            self._cells.append(row_cells)
            self._row_splitters.append(row_spl)
            self._outer_splitter.addWidget(row_spl)
            row_spl.setSizes([1000] * self._cols)
        self._outer_splitter.setSizes([1000] * self._rows)

    def _create_cell(self, row: int, col: int) -> DashboardCell:
        cell = DashboardCell(row, col)
        cell.widget_added.connect(
            lambda wt, s, r=row, c=col: self._on_cell_widget_added(r, c, wt, s)
        )
        cell.widget_removed.connect(
            lambda r=row, c=col: self._on_cell_widget_removed(r, c)
        )
        return cell

    def _on_cell_widget_added(self, row: int, col: int, widget_type: str, settings: dict):
        cell = self.cell_at(row, col)
        if cell and cell.widget:
            self._cell_widgets[(row, col)] = cell.widget
            if self._datasets and hasattr(cell.widget, 'set_datasets'):
                cell.widget.set_datasets(self._datasets)
            elif self._df is not None and hasattr(cell.widget, 'set_data'):
                cell.widget.set_data(self._df)
        self.widget_added.emit(row, col, widget_type, settings)
        self.grid_changed.emit()

    def _on_cell_widget_removed(self, row: int, col: int):
        self._cell_widgets.pop((row, col), None)
        self.widget_removed.emit(row, col)
        self.grid_changed.emit()
