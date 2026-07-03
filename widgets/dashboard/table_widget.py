# widgets/dashboard/table_widget.py
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy
)

from widgets.dashboard.base_widget import BaseDashboardWidget

# Цвета в тёмной теме
_TEXT  = QColor('#e8edf2')   # светлый текст
_TEXT2 = QColor('#9da8b7')   # приглушённый текст
_BG0   = QColor('#1e2d1e')   # фон чётных строк
_BG1   = QColor('#253525')   # фон нечётных строк


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

            # Тёмная стилизация таблицы
            self._table.setStyleSheet("""
                QTableWidget {
                    background: #1a2a1a;
                    color: #e8edf2;
                    border: none;
                    gridline-color: #2e4030;
                    font-size: 11px;
                }
                QTableWidget::item {
                    padding: 2px 6px;
                    border: none;
                }
                QTableWidget::item:selected {
                    background: #2e5c30;
                    color: #e8edf2;
                }
                QHeaderView::section {
                    background: #0f1f0f;
                    color: #7fb87f;
                    border: none;
                    border-bottom: 1px solid #2e4030;
                    padding: 3px 6px;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)

            hh = self._table.horizontalHeader()
            hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            hh.setSectionResizeMode(1, QHeaderView.Stretch)
            hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)

            self._table.verticalHeader().setDefaultSectionSize(24)
            self._table.verticalHeader().setVisible(False)
            self._table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self._table.setMinimumHeight(60)
            self._content_layout.addWidget(self._table)

        self._apply_settings()

    def _apply_settings(self):
        """Применяет настройки и заполняет таблицу."""
        if self._table is None:
            return
        try:
            limit = int(self._settings.get('limit', 5))
            rows  = min(max(1, limit), 50)

            self._table.setRowCount(rows)
            for i in range(rows):
                bg = _BG0 if i % 2 == 0 else _BG1

                num_item = QTableWidgetItem(str(i + 1))
                num_item.setForeground(_TEXT2)
                num_item.setBackground(bg)
                num_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)

                name_item = QTableWidgetItem(f"Показатель {i + 1}")
                name_item.setForeground(_TEXT)
                name_item.setBackground(bg)

                val_item = QTableWidgetItem("—")
                val_item.setForeground(_TEXT2)
                val_item.setBackground(bg)
                val_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)

                self._table.setItem(i, 0, num_item)
                self._table.setItem(i, 1, name_item)
                self._table.setItem(i, 2, val_item)

            # Ограничиваем высоту, чтобы не «выдавить» другие ячейки
            row_h    = self._table.rowHeight(0) if rows else 24
            header_h = self._table.horizontalHeader().height()
            max_vis  = min(rows, 8)
            self._table.setMaximumHeight(header_h + row_h * max_vis + 4)

        except Exception:
            import traceback; traceback.print_exc()

    def refresh(self):
        self._apply_settings()
