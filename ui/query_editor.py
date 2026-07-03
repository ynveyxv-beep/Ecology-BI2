# ui/query_editor.py
"""
Редактор / предобработчик данных — аналог Power Query.
Позволяет просматривать и трансформировать датасет перед визуализацией.
Каждое действие добавляет «шаг» в список Applied Steps; шаги можно отменить.
"""

import pandas as pd
import numpy as np

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor, QBrush, QAction
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLabel, QFrame, QListWidget, QListWidgetItem,
    QTableView, QHeaderView, QAbstractItemView, QMenu,
    QInputDialog, QMessageBox, QComboBox, QLineEdit,
    QFormLayout, QDialogButtonBox, QCheckBox, QScrollArea,
    QApplication
)

from ui.theme import (
    BG_DEEP, BG_DARK, BG_PANEL, BG_CARD, BG_HOVER, BG_ACTIVE,
    BORDER, BORDER_LT, BORDER_ACC,
    TEXT_PRI, TEXT_SEC, TEXT_MUT,
    ACCENT, ACCENT_DARK, ACCENT_RED, scrollbar_style
)


# ─── Pandas Table Model ───────────────────────────────────────────────────────

_NA_BG   = QColor("#3a2020")
_NA_FG   = QColor("#F44336")
_ODD_BG  = QColor(BG_CARD)
_EVEN_BG = QColor(BG_DEEP)


class PandasTableModel(QAbstractTableModel):
    """QAbstractTableModel обёртка над pandas DataFrame."""

    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)
        self._df = df.reset_index(drop=True)

    def update(self, df: pd.DataFrame):
        self.beginResetModel()
        self._df = df.reset_index(drop=True)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._df)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._df.columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        value = self._df.iat[row, col]

        try:
            is_na = bool(pd.isna(value))
        except (TypeError, ValueError):
            is_na = False

        if role == Qt.DisplayRole:
            if is_na:
                return "∅"
            if isinstance(value, float):
                s = f"{value:,.6f}".rstrip('0').rstrip('.')
                return s
            return str(value)

        if role == Qt.BackgroundRole:
            return QBrush(_NA_BG if is_na else (_ODD_BG if row % 2 else _EVEN_BG))

        if role == Qt.ForegroundRole:
            return QBrush(_NA_FG if is_na else QColor(TEXT_SEC))

        if role == Qt.TextAlignmentRole:
            if isinstance(value, (int, float)) and not is_na:
                return int(Qt.AlignRight | Qt.AlignVCenter)
            return int(Qt.AlignLeft | Qt.AlignVCenter)

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                col_name = str(self._df.columns[section])
                dtype    = str(self._df.dtypes.iloc[section])
                return f"{col_name}\n{dtype}"
            return str(section + 1)
        if role == Qt.ForegroundRole:
            return QBrush(QColor(TEXT_PRI))
        return None


# ─── Класс шага трансформации ────────────────────────────────────────────────

class _Step:
    def __init__(self, name: str, fn):
        self.name = name
        self._fn  = fn

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._fn(df.copy())


# ─── Общий стиль диалогов ────────────────────────────────────────────────────

def _dlg_css() -> str:
    return (
        f"QDialog{{background:{BG_DARK};}}"
        f"QLabel{{color:{TEXT_PRI};background:transparent;}}"
        f"QLineEdit{{background:{BG_CARD};border:1px solid {BORDER};border-radius:5px;"
        f"padding:5px 8px;color:{TEXT_PRI};}}"
        f"QLineEdit:focus{{border-color:{BORDER_ACC};}}"
        f"QComboBox{{background:{BG_CARD};border:1px solid {BORDER};border-radius:5px;"
        f"padding:4px 8px;color:{TEXT_PRI};}}"
        f"QComboBox QAbstractItemView{{background:{BG_CARD};color:{TEXT_PRI};"
        f"selection-background-color:{BG_ACTIVE};}}"
        f"QCheckBox{{color:{TEXT_SEC};padding:3px 0;}}"
    )


def _make_btn(text: str, accent: bool = False) -> QPushButton:
    b = QPushButton(text)
    if accent:
        b.setStyleSheet(
            f"QPushButton{{background:{ACCENT_DARK};color:{TEXT_PRI};border:none;"
            f"border-radius:5px;padding:6px 18px;font-size:12px;}}"
            f"QPushButton:hover{{background:{ACCENT};color:#0F1A0F;}}"
        )
    else:
        b.setStyleSheet(
            f"QPushButton{{background:{BG_CARD};border:1px solid {BORDER};"
            f"border-radius:5px;padding:6px 18px;font-size:12px;color:{TEXT_SEC};}}"
            f"QPushButton:hover{{background:{BG_HOVER};border-color:{BORDER_LT};}}"
        )
    return b


# ─── Вспомогательные диалоги ─────────────────────────────────────────────────

class _FilterDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Фильтр строк")
        self.setStyleSheet(_dlg_css())
        self.setFixedSize(370, 210)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)
        form = QFormLayout(); form.setSpacing(8)
        self._col = QComboBox(); self._col.addItems([str(c) for c in columns])
        self._op  = QComboBox()
        self._op.addItems(["==", "!=", ">", ">=", "<", "<=", "содержит", "начинается с"])
        self._val = QLineEdit(); self._val.setPlaceholderText("Значение…")
        form.addRow("Столбец:", self._col)
        form.addRow("Условие:", self._op)
        form.addRow("Значение:", self._val)
        lay.addLayout(form)
        row = QHBoxLayout()
        ok = _make_btn("Применить", True); cn = _make_btn("Отмена")
        ok.clicked.connect(self.accept); cn.clicked.connect(self.reject)
        row.addWidget(cn); row.addWidget(ok)
        lay.addLayout(row)

    def values(self):
        return self._col.currentText(), self._op.currentText(), self._val.text().strip()


class _FillNaDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Заполнить пустые значения")
        self.setStyleSheet(_dlg_css())
        self.setFixedSize(380, 240)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)
        form = QFormLayout(); form.setSpacing(8)
        self._col = QComboBox()
        self._col.addItems(["— Все столбцы —"] + [str(c) for c in columns])
        self._method = QComboBox()
        self._method.addItems([
            "Константа", "Среднее (mean)", "Медиана (median)",
            "Мода (mode)", "Предыдущее (ffill)", "Следующее (bfill)"
        ])
        self._val = QLineEdit(); self._val.setPlaceholderText("Значение (для Константы)…")
        self._method.currentIndexChanged.connect(lambda i: self._val.setEnabled(i == 0))
        form.addRow("Столбец:", self._col)
        form.addRow("Метод:", self._method)
        form.addRow("Значение:", self._val)
        lay.addLayout(form)
        row = QHBoxLayout()
        ok = _make_btn("Применить", True); cn = _make_btn("Отмена")
        ok.clicked.connect(self.accept); cn.clicked.connect(self.reject)
        row.addWidget(cn); row.addWidget(ok)
        lay.addLayout(row)

    def values(self):
        col = self._col.currentText()
        return (None if col.startswith("—") else col), self._method.currentText(), self._val.text().strip()


class _TypeDialog(QDialog):
    def __init__(self, columns, preset=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Изменить тип данных")
        self.setStyleSheet(_dlg_css())
        self.setFixedSize(350, 170)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)
        form = QFormLayout(); form.setSpacing(8)
        self._col  = QComboBox(); self._col.addItems([str(c) for c in columns])
        self._type = QComboBox()
        self._type.addItems(["Число (float)", "Целое (int)", "Текст (str)", "Дата (datetime)"])
        if preset:
            self._col.setCurrentText(str(preset))
        form.addRow("Столбец:", self._col)
        form.addRow("Новый тип:", self._type)
        lay.addLayout(form)
        row = QHBoxLayout()
        ok = _make_btn("Применить", True); cn = _make_btn("Отмена")
        ok.clicked.connect(self.accept); cn.clicked.connect(self.reject)
        row.addWidget(cn); row.addWidget(ok)
        lay.addLayout(row)

    def values(self):
        return self._col.currentText(), self._type.currentText()


class _RemoveColsDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Удалить столбцы")
        self.setStyleSheet(_dlg_css())
        self.setFixedSize(320, 380)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)
        lay.addWidget(QLabel("Выберите столбцы для удаления:"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        inner = QWidget(); inner.setStyleSheet("background:transparent;")
        inner_l = QVBoxLayout(inner)
        inner_l.setContentsMargins(0, 0, 0, 0); inner_l.setSpacing(2)
        self._checks = []
        for col in columns:
            cb = QCheckBox(str(col))
            inner_l.addWidget(cb); self._checks.append(cb)
        inner_l.addStretch()
        scroll.setWidget(inner)
        lay.addWidget(scroll, 1)
        row = QHBoxLayout()
        ok = _make_btn("Удалить", True); cn = _make_btn("Отмена")
        ok.clicked.connect(self.accept); cn.clicked.connect(self.reject)
        row.addWidget(cn); row.addWidget(ok)
        lay.addLayout(row)

    def selected(self):
        return [cb.text() for cb in self._checks if cb.isChecked()]


class _SortDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Сортировка")
        self.setStyleSheet(_dlg_css())
        self.setFixedSize(330, 165)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)
        form = QFormLayout(); form.setSpacing(8)
        self._col = QComboBox(); self._col.addItems([str(c) for c in columns])
        self._dir = QComboBox(); self._dir.addItems(["По возрастанию ↑", "По убыванию ↓"])
        form.addRow("Столбец:", self._col)
        form.addRow("Порядок:", self._dir)
        lay.addLayout(form)
        row = QHBoxLayout()
        ok = _make_btn("Применить", True); cn = _make_btn("Отмена")
        ok.clicked.connect(self.accept); cn.clicked.connect(self.reject)
        row.addWidget(cn); row.addWidget(ok)
        lay.addLayout(row)

    def values(self):
        return self._col.currentText(), self._dir.currentIndex() == 0


class _CalcColDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Вычисляемый столбец")
        self.setStyleSheet(_dlg_css())
        self.setFixedSize(420, 240)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)
        form = QFormLayout(); form.setSpacing(8)
        self._name = QLineEdit(); self._name.setPlaceholderText("Имя нового столбца…")
        self._expr = QLineEdit(); self._expr.setPlaceholderText("Например: Продажи * 1.2")
        form.addRow("Имя:", self._name)
        form.addRow("Формула:", self._expr)
        lay.addLayout(form)
        cols_short = [str(c) for c in columns[:8]]
        hint = QLabel("Доступные столбцы: " + ", ".join(cols_short) + ("…" if len(columns) > 8 else ""))
        hint.setStyleSheet(f"color:{TEXT_MUT};font-size:11px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        hint2 = QLabel("Используйте Python-выражения: +  -  *  /  **")
        hint2.setStyleSheet(f"color:{TEXT_MUT};font-size:11px;")
        lay.addWidget(hint2)
        row = QHBoxLayout()
        ok = _make_btn("Создать", True); cn = _make_btn("Отмена")
        ok.clicked.connect(self.accept); cn.clicked.connect(self.reject)
        row.addWidget(cn); row.addWidget(ok)
        lay.addLayout(row)

    def values(self):
        return self._name.text().strip(), self._expr.text().strip()


class _ReplaceDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Заменить значения")
        self.setStyleSheet(_dlg_css())
        self.setFixedSize(370, 205)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)
        form = QFormLayout(); form.setSpacing(8)
        self._col    = QComboBox(); self._col.addItems(["— Весь датасет —"] + [str(c) for c in columns])
        self._search = QLineEdit(); self._search.setPlaceholderText("Найти…")
        self._repl   = QLineEdit(); self._repl.setPlaceholderText("Заменить на…")
        form.addRow("Столбец:", self._col)
        form.addRow("Найти:", self._search)
        form.addRow("Заменить:", self._repl)
        lay.addLayout(form)
        row = QHBoxLayout()
        ok = _make_btn("Заменить", True); cn = _make_btn("Отмена")
        ok.clicked.connect(self.accept); cn.clicked.connect(self.reject)
        row.addWidget(cn); row.addWidget(ok)
        lay.addLayout(row)

    def values(self):
        col = self._col.currentText()
        return (None if col.startswith("—") else col), self._search.text(), self._repl.text()


# ─── Главный диалог ───────────────────────────────────────────────────────────

class QueryEditorDialog(QDialog):
    """
    Редактор данных — аналог Power Query.
    Открывайте через QueryEditorDialog(name, df, parent).
    После accept() обращайтесь к .result_df.
    """

    def __init__(self, name: str, df: pd.DataFrame, parent=None):
        super().__init__(parent)
        self._name   = name
        self._origin = df.copy()
        self._steps: list[_Step] = []
        self.result_df = df.copy()

        self.setWindowTitle(f"Редактор данных — {name}")
        self.setModal(True)
        self.setMinimumSize(1080, 640)
        self.setStyleSheet(
            f"QDialog{{background:{BG_DARK};}}"
            f"QLabel{{color:{TEXT_PRI};}}"
            f"QListWidget{{background:{BG_DEEP};border:none;color:{TEXT_SEC};outline:none;}}"
            f"QListWidget::item{{padding:6px 12px;border-bottom:1px solid {BORDER};}}"
            f"QListWidget::item:selected{{background:{BG_ACTIVE};color:{TEXT_PRI};}}"
            f"QHeaderView::section{{background:{BG_PANEL};color:{TEXT_PRI};"
            f"border:none;border-right:1px solid {BORDER};border-bottom:1px solid {BORDER};"
            f"padding:4px 8px;font-size:11px;}}"
            f"QTableView{{gridline-color:{BORDER};border:none;background:{BG_DEEP};"
            f"selection-background-color:{BG_ACTIVE};outline:none;}}"
            f"{scrollbar_style()}"
        )

        self._build_ui()
        self._refresh_table()

    # ── Построение UI ─────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_header())
        root.addWidget(self._make_toolbar())

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1); sep.setStyleSheet(f"background:{BORDER};border:none;")
        root.addWidget(sep)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle{background:" + BORDER + ";width:1px;}")
        splitter.addWidget(self._make_steps_panel())
        splitter.addWidget(self._make_table_panel())
        splitter.setSizes([230, 850])
        root.addWidget(splitter, 1)

    def _make_header(self) -> QWidget:
        w = QWidget(); w.setFixedHeight(50)
        w.setStyleSheet(f"background:{BG_PANEL};border-bottom:1px solid {BORDER};")
        lay = QHBoxLayout(w); lay.setContentsMargins(16, 0, 16, 0)

        icon = QLabel("⚡"); icon.setStyleSheet("font-size:18px;background:transparent;border:none;")
        lay.addWidget(icon)

        title = QLabel(f"Power Query — {self._name}")
        title.setStyleSheet(f"font-size:14px;font-weight:bold;color:{TEXT_PRI};background:transparent;border:none;")
        lay.addWidget(title, 1)

        apply_btn = _make_btn("✓  Применить и закрыть", True)
        apply_btn.clicked.connect(self._apply_and_close)
        lay.addWidget(apply_btn)

        cancel_btn = _make_btn("Отмена")
        cancel_btn.clicked.connect(self.reject)
        lay.addWidget(cancel_btn)
        return w

    def _make_toolbar(self) -> QWidget:
        w = QWidget(); w.setFixedHeight(42)
        w.setStyleSheet(f"background:{BG_PANEL};border-bottom:1px solid {BORDER};")
        lay = QHBoxLayout(w); lay.setContentsMargins(10, 0, 10, 0); lay.setSpacing(3)

        _S = (
            f"QPushButton{{background:{BG_CARD};border:1px solid {BORDER};"
            f"border-radius:5px;padding:0 9px;font-size:11px;color:{TEXT_SEC};height:28px;}}"
            f"QPushButton:hover{{background:{BG_HOVER};border-color:{BORDER_LT};color:{TEXT_PRI};}}"
        )

        def tb(label, fn, tip=""):
            b = QPushButton(label); b.setStyleSheet(_S); b.setToolTip(tip)
            b.clicked.connect(fn); lay.addWidget(b); return b

        def vsep():
            s = QFrame(); s.setFrameShape(QFrame.VLine); s.setFixedSize(1, 22)
            s.setStyleSheet(f"background:{BORDER};border:none;"); lay.addWidget(s)

        tb("↩ Отменить шаг",     self._undo_step,         "Удалить последний применённый шаг")
        vsep()
        tb("✏ Переименовать",    self._rename_column,     "Переименовать столбец")
        tb("✕ Удалить столбцы", self._remove_columns,    "Выбрать и удалить столбцы")
        tb("≡ Тип данных",       self._change_type,       "Привести столбец к нужному типу")
        vsep()
        tb("▼ Фильтр строк",    self._filter_rows,       "Оставить строки по условию")
        tb("⟂ Сортировка",      self._sort_rows,         "Отсортировать по столбцу")
        tb("◫ Без дубликатов",  self._remove_duplicates, "Удалить повторяющиеся строки")
        vsep()
        tb("∅ Заполнить NA",    self._fill_na,           "Заполнить пустые ячейки")
        tb("⟳ Замена значений", self._replace_values,    "Найти и заменить значения")
        tb("+ Вычисл. столбец", self._add_calc_col,      "Добавить столбец по формуле")
        vsep()
        tb("⊞ Транспонировать", self._transpose,         "Транспонировать таблицу (строки ↔ столбцы)")
        lay.addStretch()

        return w

    def _make_steps_panel(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background:{BG_DEEP};")
        lay = QVBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)

        hdr = QLabel("  Применённые шаги")
        hdr.setFixedHeight(32)
        hdr.setStyleSheet(
            f"color:{TEXT_MUT};font-size:11px;font-weight:bold;"
            f"background:{BG_PANEL};border-bottom:1px solid {BORDER};"
        )
        lay.addWidget(hdr)

        self._steps_list = QListWidget()
        self._steps_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._steps_list.customContextMenuRequested.connect(self._steps_ctx_menu)
        lay.addWidget(self._steps_list, 1)

        origin_item = QListWidgetItem("⬤  Источник загружен")
        origin_item.setForeground(QColor(TEXT_MUT))
        self._steps_list.addItem(origin_item)
        return w

    def _make_table_panel(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background:{BG_DEEP};")
        lay = QVBoxLayout(w); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)

        self._table = QTableView()
        self._table.setAlternatingRowColors(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectColumns)
        self._table.setSortingEnabled(False)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive)
        hh.setDefaultSectionSize(140)
        hh.setContextMenuPolicy(Qt.CustomContextMenu)
        hh.customContextMenuRequested.connect(self._col_header_menu)
        self._table.verticalHeader().setDefaultSectionSize(24)
        self._table.verticalHeader().setStyleSheet(
            f"QHeaderView::section{{background:{BG_PANEL};color:{TEXT_MUT};"
            f"border:none;border-right:1px solid {BORDER};padding:2px 6px;font-size:10px;}}"
        )

        self._model = PandasTableModel(self._origin)
        self._table.setModel(self._model)
        lay.addWidget(self._table, 1)

        self._stat_lbl = QLabel()
        self._stat_lbl.setFixedHeight(26)
        self._stat_lbl.setStyleSheet(
            f"color:{TEXT_MUT};font-size:11px;padding:0 12px;"
            f"background:{BG_PANEL};border-top:1px solid {BORDER};"
        )
        lay.addWidget(self._stat_lbl)
        return w

    # ── Логика шагов ─────────────────────────────────────────────────────────

    def _current_df(self) -> pd.DataFrame:
        df = self._origin.copy()
        for step in self._steps:
            try:
                df = step.apply(df)
            except Exception:
                break
        return df

    def _refresh_table(self):
        df = self._current_df()
        self._model.update(df)
        self.result_df = df

        na_cnt   = int(df.isna().sum().sum())
        dup_cnt  = int(df.duplicated().sum())
        stat = f"  {len(df):,} строк · {len(df.columns)} столбцов"
        if na_cnt:  stat += f" · {na_cnt} пустых"
        if dup_cnt: stat += f" · {dup_cnt} дублей"
        self._stat_lbl.setText(stat)

    def _add_step(self, step: _Step):
        self._steps.append(step)
        item = QListWidgetItem(f"✓  {step.name}")
        item.setForeground(QColor(ACCENT))
        self._steps_list.addItem(item)
        self._steps_list.scrollToBottom()
        self._refresh_table()

    def _undo_step(self):
        if not self._steps:
            return
        self._steps.pop()
        cnt = self._steps_list.count()
        if cnt > 1:
            self._steps_list.takeItem(cnt - 1)
        self._refresh_table()

    def _steps_ctx_menu(self, pos):
        item = self._steps_list.itemAt(pos)
        idx  = self._steps_list.row(item) if item else -1
        if idx <= 0:
            return
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu{{background:{BG_CARD};border:1px solid {BORDER};color:{TEXT_PRI};}}"
            f"QMenu::item:selected{{background:{BG_HOVER};}}"
        )
        del_a = menu.addAction("🗑  Удалить этот шаг")
        if menu.exec(self._steps_list.mapToGlobal(pos)) == del_a:
            self._steps.pop(idx - 1)
            self._steps_list.takeItem(idx)
            self._refresh_table()

    # ── Контекстное меню заголовка ────────────────────────────────────────────

    def _col_header_menu(self, pos):
        idx = self._table.horizontalHeader().logicalIndexAt(pos)
        if idx < 0:
            return
        df  = self._current_df()
        col = str(df.columns[idx])

        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu{{background:{BG_CARD};border:1px solid {BORDER};color:{TEXT_PRI};}}"
            f"QMenu::item:selected{{background:{BG_HOVER};}}"
        )
        menu.addAction(f'  «{col}»').setEnabled(False)
        menu.addSeparator()
        a_ren  = menu.addAction("✏  Переименовать")
        a_rem  = menu.addAction("✕  Удалить")
        a_asc  = menu.addAction("⟂  Сортировать ↑")
        a_desc = menu.addAction("⟂  Сортировать ↓")
        menu.addSeparator()
        a_type = menu.addAction("≡  Изменить тип…")
        a_fill = menu.addAction("∅  Заполнить NA…")

        act = menu.exec(self._table.horizontalHeader().mapToGlobal(pos))
        if act == a_ren:   self._rename_column(col)
        elif act == a_rem: self._do_remove_cols([col])
        elif act == a_asc: self._do_sort(col, True)
        elif act == a_desc:self._do_sort(col, False)
        elif act == a_type:self._change_type(col)
        elif act == a_fill:self._fill_na(col)

    # ── Операции ──────────────────────────────────────────────────────────────

    def _rename_column(self, preset: str = None):
        df = self._current_df()
        if preset is None:
            col, ok = QInputDialog.getItem(
                self, "Переименовать", "Выберите столбец:",
                [str(c) for c in df.columns], 0, False
            )
            if not ok: return
        else:
            col = preset

        new, ok = QInputDialog.getText(self, "Новое имя", f"Новое имя для «{col}»:", text=col)
        if not ok or not new.strip() or new.strip() == col: return
        new = new.strip()
        self._add_step(_Step(
            f"Переименовать: «{col}» → «{new}»",
            lambda d, c=col, n=new: d.rename(columns={c: n})
        ))

    def _remove_columns(self):
        df = self._current_df()
        dlg = _RemoveColsDialog([str(c) for c in df.columns], self)
        if dlg.exec() != QDialog.Accepted: return
        cols = dlg.selected()
        if not cols: return
        self._do_remove_cols(cols)

    def _do_remove_cols(self, cols: list):
        self._add_step(_Step(
            f"Удалить: {', '.join(cols)}",
            lambda d, c=cols: d.drop(columns=[x for x in c if x in d.columns], errors='ignore')
        ))

    def _change_type(self, preset: str = None):
        df  = self._current_df()
        dlg = _TypeDialog([str(c) for c in df.columns], preset=preset, parent=self)
        if dlg.exec() != QDialog.Accepted: return
        col, type_str = dlg.values()

        _converters = {
            "Число (float)":   lambda s: pd.to_numeric(s, errors='coerce'),
            "Целое (int)":     lambda s: pd.to_numeric(s, errors='coerce').astype('Int64'),
            "Текст (str)":     lambda s: s.astype(str),
            "Дата (datetime)": lambda s: pd.to_datetime(s, errors='coerce', dayfirst=True),
        }
        conv = _converters[type_str]
        type_short = type_str.split(" ")[0].lower()

        def _apply(d, c=col, fn=conv):
            d = d.copy(); d[c] = fn(d[c]); return d

        self._add_step(_Step(f"Тип «{col}» → {type_short}", _apply))

    def _filter_rows(self):
        df = self._current_df()
        dlg = _FilterDialog([str(c) for c in df.columns], self)
        if dlg.exec() != QDialog.Accepted: return
        col, op, val = dlg.values()
        if not val and op not in ("содержит", "начинается с"): return

        def _apply(d, c=col, o=op, v=val):
            s = d[c]
            # Пробуем числовое сравнение
            try:
                num = float(v)
                sn = pd.to_numeric(s, errors='coerce')
                masks = {"==": sn==num, "!=": sn!=num, ">": sn>num,
                         ">=": sn>=num, "<": sn<num, "<=": sn<=num}
                if o in masks: return d[masks[o]]
            except (ValueError, TypeError):
                pass
            # Строковое сравнение
            ss = s.astype(str)
            if o == "==":           return d[ss == v]
            if o == "!=":           return d[ss != v]
            if o == "содержит":     return d[ss.str.contains(v, case=False, na=False)]
            if o == "начинается с": return d[ss.str.startswith(v, na=False)]
            return d

        self._add_step(_Step(f"Фильтр: {col} {op} {val}", _apply))

    def _sort_rows(self):
        df = self._current_df()
        dlg = _SortDialog([str(c) for c in df.columns], self)
        if dlg.exec() != QDialog.Accepted: return
        col, asc = dlg.values()
        direction = "↑" if asc else "↓"
        self._add_step(_Step(
            f"Сортировка: {col} {direction}",
            lambda d, c=col, a=asc: d.sort_values(by=c, ascending=a).reset_index(drop=True)
        ))

    def _do_sort(self, col: str, ascending: bool):
        direction = "↑" if ascending else "↓"
        self._add_step(_Step(
            f"Сортировка: {col} {direction}",
            lambda d, c=col, a=ascending: d.sort_values(by=c, ascending=a).reset_index(drop=True)
        ))

    def _remove_duplicates(self):
        df_before = self._current_df()
        self._add_step(_Step(
            "Удалить дубликаты",
            lambda d: d.drop_duplicates().reset_index(drop=True)
        ))
        removed = len(df_before) - len(self._current_df())
        if removed == 0:
            QMessageBox.information(self, "Дубликаты", "Дубликатов не найдено.")

    def _fill_na(self, preset_col: str = None):
        df = self._current_df()
        dlg = _FillNaDialog([str(c) for c in df.columns], self)
        if preset_col: dlg._col.setCurrentText(str(preset_col))
        if dlg.exec() != QDialog.Accepted: return
        col, method, const = dlg.values()

        def _apply(d, c=col, m=method, v=const):
            target_cols = [c] if c else list(d.columns)
            d = d.copy()
            for cc in target_cols:
                if "Константа" in m:
                    d[cc] = d[cc].fillna(v)
                elif "mean" in m:
                    d[cc] = d[cc].fillna(pd.to_numeric(d[cc], errors='coerce').mean())
                elif "median" in m:
                    d[cc] = d[cc].fillna(pd.to_numeric(d[cc], errors='coerce').median())
                elif "mode" in m:
                    mo = d[cc].mode()
                    if not mo.empty: d[cc] = d[cc].fillna(mo.iloc[0])
                elif "ffill" in m:
                    d[cc] = d[cc].ffill()
                elif "bfill" in m:
                    d[cc] = d[cc].bfill()
            return d

        col_label = col if col else "все столбцы"
        self._add_step(_Step(f"Заполнить NA: {col_label} ({method})", _apply))

    def _replace_values(self):
        df = self._current_df()
        dlg = _ReplaceDialog([str(c) for c in df.columns], self)
        if dlg.exec() != QDialog.Accepted: return
        col, search, repl = dlg.values()
        if search == "": return

        def _apply(d, c=col, s=search, r=repl):
            d = d.copy()
            if c:
                d[c] = d[c].astype(str).str.replace(s, r, regex=False)
            else:
                for cc in d.columns:
                    try: d[cc] = d[cc].astype(str).str.replace(s, r, regex=False)
                    except: pass
            return d

        col_label = col if col else "весь датасет"
        self._add_step(_Step(f"Заменить «{search}»→«{repl}» в {col_label}", _apply))

    def _add_calc_col(self):
        df = self._current_df()
        dlg = _CalcColDialog([str(c) for c in df.columns], self)
        if dlg.exec() != QDialog.Accepted: return
        name, expr = dlg.values()
        if not name or not expr: return

        # Предварительная проверка
        try:
            result = df.eval(expr)
            assert len(result) == len(df)
        except Exception as exc:
            QMessageBox.warning(self, "Ошибка формулы", f"Не удалось вычислить выражение:\n{exc}")
            return

        self._add_step(_Step(
            f"Новый столбец «{name}» = {expr}",
            lambda d, n=name, ex=expr: d.assign(**{n: d.eval(ex)})
        ))

    def _transpose(self):
        df = self._current_df()
        reply = QMessageBox.question(
            self, "Транспонировать таблицу",
            f"Таблица будет транспонирована:\n"
            f"  {len(df)} строк × {len(df.columns)} столбцов  →  "
            f"{len(df.columns)} строк × {len(df)} столбцов\n\n"
            "Текущий индекс станет заголовками, а заголовки — первым столбцом.",
            QMessageBox.Ok | QMessageBox.Cancel,
            QMessageBox.Ok,
        )
        if reply != QMessageBox.Ok:
            return

        def do_transpose(d: pd.DataFrame) -> pd.DataFrame:
            t = d.T.reset_index()
            t.columns = [f"col_{i}" if i > 0 else "index" for i in range(len(t.columns))]
            # Попытаться использовать первую строку как заголовки
            if len(t) > 0:
                new_cols = [str(v) for v in t.iloc[0]]
                t = t.iloc[1:].reset_index(drop=True)
                t.columns = new_cols
            return t

        self._add_step(_Step("Транспонировать таблицу", do_transpose))

    # ── Применить ─────────────────────────────────────────────────────────────

    def _apply_and_close(self):
        self.result_df = self._current_df()
        self.accept()
