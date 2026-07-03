# widgets/grid/dashboard_cell.py
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QLabel, QMessageBox
)
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from widgets.factory.dashboard_widget_factory import DashboardWidgetFactory
from ui.theme import (
    BG_CARD, BG_DARK, BG_HOVER, BG_ACTIVE, BG_PANEL,
    BORDER, BORDER_LT, BORDER_ACC,
    TEXT_PRI, TEXT_SEC, TEXT_MUT,
    ACCENT, ACCENT_RED
)

MIME_WIDGET_TYPE = "application/x-dashboard-widget-type"


class DashboardCell(QFrame):
    """
    Ячейка сетки конструктора.

    Состояния:
    - Пустая: большой «+» с подсказкой, реагирует на клик / drag-and-drop
    - Занятая: отображает виджет с мини-тулбаром (✎ / ✕)

    Сигналы:
    - widget_added(тип, настройки) — когда виджет создан
    - widget_removed() — когда виджет удалён
    """

    widget_added   = Signal(str, dict)
    widget_removed = Signal()

    _STYLE_EMPTY = f"""
        QFrame#cell_empty {{
            background: {BG_CARD};
            border: 2px dashed {BORDER_LT};
            border-radius: 6px;
            min-height: 140px;
            min-width: 140px;
        }}
        QFrame#cell_empty:hover {{
            border-color: {BORDER_ACC};
            background: {BG_HOVER};
        }}
    """
    _STYLE_FILLED = f"""
        QFrame#cell_filled {{
            background: {BG_DARK};
            border: 1px solid {BORDER};
            border-radius: 6px;
        }}
    """

    def __init__(self, row: int, col: int, parent=None):
        super().__init__(parent)
        self.row = row
        self.col = col
        self._widget = None
        self._widget_type = None
        self._master = None   # (row, col) of spanning widget that covers this cell
        self._datasets: dict = {}   # глобальные датасеты, передаются из grid

        self.setAcceptDrops(True)
        self.setObjectName("cell_empty")
        self.setStyleSheet(self._STYLE_EMPTY)

        self._layout = QVBoxLayout(self)
        self._layout.setAlignment(Qt.AlignCenter)
        self._layout.setContentsMargins(6, 6, 6, 6)
        self._layout.setSpacing(0)

        self._show_empty_state()

    # ─── Свойства ──────────────────────────────────────────────────────────

    @property
    def is_empty(self) -> bool:
        return self._widget is None

    @property
    def widget_type(self) -> str:
        return self._widget_type

    @property
    def widget(self) -> QWidget:
        return self._widget

    # ─── Публичные методы ──────────────────────────────────────────────────

    def set_widget(self, widget: QWidget, widget_type: str) -> None:
        """Устанавливает виджет в ячейку, заменяя пустое состояние."""
        self._clear_layout()
        self._widget      = widget
        self._widget_type = widget_type

        # В заполненном состоянии — убираем выравнивание, чтобы виджет растягивался
        self._layout.setAlignment(Qt.Alignment())

        # Тулбар с названием типа + кнопки ✎ / ✕
        toolbar = self._build_toolbar(widget_type)
        self._layout.addWidget(toolbar)
        self._layout.addWidget(widget, 1)

        self.setObjectName("cell_filled")
        self.setStyleSheet(self._STYLE_FILLED)

        if hasattr(widget, 'edit_requested'):
            widget.edit_requested.connect(self._on_edit_requested)

    def set_blocked(self, master_row: int, master_col: int) -> None:
        """Ячейка перекрыта виджетом-спаном из (master_row, master_col)."""
        self._clear_layout()
        self._master = (master_row, master_col)
        self.setAcceptDrops(False)
        self.setObjectName("cell_blocked")
        self.setStyleSheet(f"""
            QFrame#cell_blocked {{
                background: {BG_PANEL};
                border: 1px dashed {BORDER};
                border-radius: 6px;
            }}
        """)

    def set_unblocked(self) -> None:
        """Восстанавливает ячейку в пустое состояние."""
        self._master = None
        self.setAcceptDrops(True)
        self._show_empty_state()
        self.setObjectName("cell_empty")
        self.setStyleSheet(self._STYLE_EMPTY)

    def clear(self) -> None:
        """Очищает ячейку и возвращает в пустое состояние."""
        self._remove_widget()
        self._show_empty_state()
        self.setObjectName("cell_empty")
        self.setStyleSheet(self._STYLE_EMPTY)
        self.widget_removed.emit()

    def get_settings(self) -> dict:
        if self._widget and hasattr(self._widget, 'settings'):
            return self._widget.settings()
        return {}

    def refresh_theme(self) -> None:
        """Перегенерирует стили из текущей темы и применяет к ячейке."""
        import ui.theme as tm
        DashboardCell._STYLE_EMPTY = f"""
            QFrame#cell_empty {{
                background: {tm.BG_CARD};
                border: 2px dashed {tm.BORDER_LT};
                border-radius: 6px;
                min-height: 140px;
                min-width: 140px;
            }}
            QFrame#cell_empty:hover {{
                border-color: {tm.BORDER_ACC};
                background: {tm.BG_HOVER};
            }}
        """
        DashboardCell._STYLE_FILLED = f"""
            QFrame#cell_filled {{
                background: {tm.BG_DARK};
                border: 1px solid {tm.BORDER};
                border-radius: 6px;
            }}
        """
        name = self.objectName()
        if name == "cell_empty":
            self.setStyleSheet(self._STYLE_EMPTY)
        elif name == "cell_filled":
            self.setStyleSheet(self._STYLE_FILLED)
        elif name == "cell_blocked":
            self.setStyleSheet(f"""
                QFrame#cell_blocked {{
                    background: {tm.BG_PANEL};
                    border: 1px dashed {tm.BORDER};
                    border-radius: 6px;
                }}
            """)

    # ─── Пустое состояние ──────────────────────────────────────────────────

    def _show_empty_state(self):
        self._clear_layout()
        self._layout.setContentsMargins(12, 12, 12, 12)

        container = QWidget()
        container.setAttribute(Qt.WA_TransparentForMouseEvents)
        vbox = QVBoxLayout(container)
        vbox.setAlignment(Qt.AlignCenter)
        vbox.setSpacing(8)

        plus = QLabel("+")
        plus.setAlignment(Qt.AlignCenter)
        plus.setStyleSheet(
            f"font-size: 36px; font-weight: 200; color: {BORDER_ACC};"
            " background: transparent; border: none;"
        )
        vbox.addWidget(plus)

        hint = QLabel("Нажмите, чтобы добавить блок")
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"font-size: 11px; color: {TEXT_MUT};"
            " background: transparent; border: none;"
        )
        vbox.addWidget(hint)

        dnd = QLabel("или перетащите тип из палитры")
        dnd.setAlignment(Qt.AlignCenter)
        dnd.setStyleSheet(
            f"font-size: 10px; color: {BORDER};"
            " background: transparent; border: none;"
        )
        vbox.addWidget(dnd)

        self._layout.addWidget(container)

    def _build_toolbar(self, widget_type: str) -> QWidget:
        """Мини-панель над виджетом: метка типа + кнопки ✎ / ✕."""
        TYPE_LABELS = {
            'kpi':   '📊 Число',
            'chart': '📈 График',
            'table': '📋 Таблица',
            'text':  '📝 Текст',
            'image': '🖼 Изображение',
            'map':   '🗺 Карта',
        }
        bar = QWidget()
        bar.setStyleSheet(
            f"QWidget {{ background:{BG_PANEL}; border-radius:6px 6px 0 0; border:none; }}"
        )
        h = QHBoxLayout(bar)
        h.setContentsMargins(8, 4, 4, 4)
        h.setSpacing(4)

        lbl = QLabel(TYPE_LABELS.get(widget_type, widget_type))
        lbl.setStyleSheet(
            f"font-size:10px; color:{TEXT_MUT}; font-weight:600; background:transparent;"
        )
        h.addWidget(lbl)
        h.addStretch()

        for icon, slot in [('✎', self._on_edit_requested), ('✕', self._on_remove_clicked)]:
            btn = QPushButton(icon)
            btn.setFixedSize(22, 22)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; border: none;
                    font-size: 13px; color: {BORDER_LT};
                }}
                QPushButton:hover {{ color: {ACCENT}; background: {BG_HOVER}; border-radius: 4px; }}
            """)
            btn.clicked.connect(slot)
            h.addWidget(btn)

        return bar

    # ─── Клик по пустой ячейке ─────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_empty and self._master is None:
            self._open_dialog()
        super().mousePressEvent(event)

    def set_datasets(self, datasets: dict):
        self._datasets = datasets

    def _open_dialog(self, preset_type: str = None):
        from widgets.dialogs.widget_creation_dialog import WidgetCreationDialog
        dialog = WidgetCreationDialog(self, preset_type=preset_type, datasets=self._datasets)
        dialog.widget_created.connect(self._on_widget_created)
        dialog.exec()

    def _on_widget_created(self, widget_type: str, settings: dict):
        try:
            widget = DashboardWidgetFactory.create(widget_type, settings)
            self.set_widget(widget, widget_type)
            self.widget_added.emit(widget_type, settings)
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"❌ Ошибка создания виджета: {e}\n{tb}")
            QMessageBox.critical(
                self,
                "Ошибка создания блока",
                f"Не удалось создать блок «{widget_type}»:\n\n{e}\n\nПодробности в консоли."
            )

    def _on_edit_requested(self):
        """Открывает диалог редактирования текущего виджета."""
        if not self._widget:
            return
        from widgets.dialogs.widget_creation_dialog import WidgetCreationDialog
        dialog = WidgetCreationDialog(self, preset_type=self._widget_type, datasets=self._datasets)
        dialog.load_settings(self._widget_type, self.get_settings())
        dialog.widget_created.connect(self._on_widget_updated)
        dialog.exec()

    def _on_widget_updated(self, widget_type: str, settings: dict):
        """Заменяет виджет новыми настройками после редактирования."""
        try:
            widget = DashboardWidgetFactory.create(widget_type, settings)
            self._remove_widget()
            self.set_widget(widget, widget_type)
            self.widget_added.emit(widget_type, settings)
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"❌ Ошибка обновления виджета: {e}\n{tb}")
            QMessageBox.critical(
                self,
                "Ошибка обновления блока",
                f"Не удалось обновить блок:\n\n{e}"
            )

    def _on_remove_clicked(self):
        self.clear()

    # ─── Приватные методы ──────────────────────────────────────────────────

    def _clear_layout(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._layout.setContentsMargins(6, 6, 6, 6)

    def _remove_widget(self):
        if self._widget:
            self._widget.deleteLater()
            self._widget      = None
            self._widget_type = None

    # ─── Drag & Drop ───────────────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat(MIME_WIDGET_TYPE) and self.is_empty and self._master is None:
            event.acceptProposedAction()
            self.setStyleSheet(
                self._STYLE_EMPTY.replace(BORDER_LT, BORDER_ACC)
                                 .replace(BG_HOVER, BG_ACTIVE)
            )
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        if self.is_empty:
            self.setStyleSheet(self._STYLE_EMPTY)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasFormat(MIME_WIDGET_TYPE) and self.is_empty:
            widget_type = bytes(
                event.mimeData().data(MIME_WIDGET_TYPE)
            ).decode('utf-8')
            self.setStyleSheet(self._STYLE_EMPTY)
            self._open_dialog(preset_type=widget_type)
            event.acceptProposedAction()
        else:
            event.ignore()
