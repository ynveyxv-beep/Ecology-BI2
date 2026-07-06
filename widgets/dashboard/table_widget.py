# widgets/dashboard/table_widget.py
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy
)

from widgets.dashboard.base_widget import BaseDashboardWidget
# BUG 6 FIX: import get_palette so we can apply theme colours at runtime
from ui.theme import get_palette


class TableWidget(BaseDashboardWidget):
    """Виджет для отображения таблицы данных."""

    def __init__(self, settings: dict = None, parent=None):
        # ВАЖНО: инициализируем _table до super().__init__(),
        # потому что BaseDashboardWidget.__init__ вызывает _apply_settings().
        self._table = None
        super().__init__(settings, parent)

        if self._table is None:
            self._table = QTableWidget()
            self._table.setColumnCount(3)
            self._table.setHorizontalHeaderLabels(["№", "Показатель", "Значение"])

            hh = self._table.horizontalHeader()
            hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            hh.setSectionResizeMode(1, QHeaderView.Stretch)
            hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)

            self._table.verticalHeader().setDefaultSectionSize(24)
            self._table.verticalHeader().setVisible(False)
            self._table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self._table.setMinimumHeight(60)
            self._content_layout.addWidget(self._table)

        self._apply_theme_style()
        self._apply_settings()

    def _apply_theme_style(self):
        """BUG 6 FIX: apply colours from current theme palette instead of hardcoded greens."""
        p = get_palette()
        bg0  = p['BG_CARD']
        bg1  = p['BG_PANEL']
        text = p['TEXT_PRI']
        text2= p['TEXT_SEC']
        acc  = p['ACCENT']
        bdr  = p['BORDER']
        active = p['BG_ACTIVE']
        header_bg = p['BG_DARK'] if 'BG_DARK' in p else p['BG_PANEL']

        self._theme_bg0   = QColor(bg0)
        self._theme_bg1   = QColor(bg1)
        self._theme_text  = QColor(text)
        self._theme_text2 = QColor(text2)

        if self._table:
            self._table.setStyleSheet(f"""
                QTableWidget {{
                    background: {bg0};
                    color: {text};
                    border: none;
                    gridline-color: {bdr};
                    font-size: 11px;
                }}
                QTableWidget::item {{
                    padding: 2px 6px;
                    border: none;
                }}
                QTableWidget::item:selected {{
                    background: {active};
                    color: {acc};
                }}
                QHeaderView::section {{
                    background: {header_bg};
                    color: {text2};
                    border: none;
                    border-bottom: 1px solid {bdr};
                    padding: 3px 6px;
                    font-size: 10px;
                    font-weight: bold;
                }}
            """)

    def _apply_settings(self):
        """Применяет настройки и заполняет таблицу."""
        if self._table is None:
            return
        try:
            # BUG 6 FIX: re-apply theme style on every settings update so theme changes stick
            self._apply_theme_style()

            limit = int(self._settings.get('limit', 5))
            rows  = min(max(1, limit), 50)

            # BUG 6 FIX: if a dataset is loaded, display actual data from it
            df = self._df
            data_source = self._settings.get('data_source', 'none')

            if df is not None and data_source != 'none':
                try:
                    # Show the first two columns of the dataframe
                    cols = df.columns.tolist()
                    label_col = cols[0] if len(cols) > 0 else None
                    val_col   = cols[1] if len(cols) > 1 else None
                    subset = df.dropna(subset=[label_col] if label_col else []).head(rows)

                    self._table.setRowCount(len(subset))
                    self._table.setHorizontalHeaderLabels(
                        ["№", label_col or "Показатель", val_col or "Значение"]
                    )
                    for i, (_, row_data) in enumerate(subset.iterrows()):
                        bg = self._theme_bg0 if i % 2 == 0 else self._theme_bg1

                        num_item = QTableWidgetItem(str(i + 1))
                        num_item.setForeground(self._theme_text2)
                        num_item.setBackground(bg)
                        num_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)

                        name_item = QTableWidgetItem(str(row_data[label_col]) if label_col else f"Строка {i+1}")
                        name_item.setForeground(self._theme_text)
                        name_item.setBackground(bg)

                        val_str = str(row_data[val_col]) if val_col and val_col in row_data.index else "—"
                        val_item = QTableWidgetItem(val_str)
                        val_item.setForeground(self._theme_text2)
                        val_item.setBackground(bg)
                        val_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)

                        self._table.setItem(i, 0, num_item)
                        self._table.setItem(i, 1, name_item)
                        self._table.setItem(i, 2, val_item)

                    self._update_table_height(len(subset))
                    return
                except Exception:
                    pass  # fall through to placeholder

            # Placeholder rows when no data is available
            self._table.setRowCount(rows)
            self._table.setHorizontalHeaderLabels(["№", "Показатель", "Значение"])
            for i in range(rows):
                bg = self._theme_bg0 if i % 2 == 0 else self._theme_bg1

                num_item = QTableWidgetItem(str(i + 1))
                num_item.setForeground(self._theme_text2)
                num_item.setBackground(bg)
                num_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)

                name_item = QTableWidgetItem(f"Показатель {i + 1}")
                name_item.setForeground(self._theme_text)
                name_item.setBackground(bg)

                val_item = QTableWidgetItem("—")
                val_item.setForeground(self._theme_text2)
                val_item.setBackground(bg)
                val_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)

                self._table.setItem(i, 0, num_item)
                self._table.setItem(i, 1, name_item)
                self._table.setItem(i, 2, val_item)

            self._update_table_height(rows)

        except Exception:
            import traceback; traceback.print_exc()

    def _update_table_height(self, row_count: int):
        """Constrains table height so it doesn't push other cells."""
        if self._table is None or row_count == 0:
            return
        row_h    = self._table.rowHeight(0) if row_count else 24
        header_h = self._table.horizontalHeader().height()
        max_vis  = min(row_count, 8)
        self._table.setMaximumHeight(header_h + row_h * max_vis + 4)

    def refresh(self):
        self._apply_settings()
