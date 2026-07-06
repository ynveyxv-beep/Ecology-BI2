# ui/configurator_window.py
"""
Конструктор дашбордов — полный рефакторинг:
  - Многостраничные дашборды (вкладки как в браузере)
  - Глобальный менеджер датасетов
  - Боковая палитра виджетов (drag & drop)
  - Каждый виджет выбирает свой датасет
"""

import os
import json
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QStackedWidget,
    QInputDialog, QFrame, QSizePolicy, QDialog,
    QListWidget, QListWidgetItem, QDialogButtonBox
)

from logger import logger, LoggerMixin
from widgets.grid.dashboard_grid import DashboardGrid
from widgets.dialogs.widget_creation_dialog import WidgetCreationDialog
from widgets.factory.dashboard_widget_factory import DashboardWidgetFactory
from exporters.html_exporter import export_to_html
from exporters.report_exporter import export_report
from widgets.dialogs.report_dialog import ReportDialog
from ui.dataset_manager import DatasetManager
import ui.theme as _tm
from ui.theme import (
    BG_DEEP, BG_DARK, BG_PANEL, BG_CARD, BG_HOVER, BG_ACTIVE,
    BORDER, BORDER_LT, BORDER_ACC,
    TEXT_PRI, TEXT_SEC, TEXT_MUT,
    ACCENT, ACCENT_DARK, ACCENT_RED,
    THEME_LIST, CURRENT_THEME_NAME, set_active_theme,
)
from PySide6.QtWidgets import QComboBox


# ─── Кастомная панель вкладок ─────────────────────────────────────────────────

class PageTabBar(QWidget):
    """
    Горизонтальная панель вкладок (страниц дашборда).
    Поддерживает переименование двойным кликом, закрытие ✕, добавление «+».
    """

    tab_selected = Signal(int)
    tab_closed   = Signal(int)
    tab_added    = Signal()
    tab_renamed  = Signal(int, str)

    _NORMAL = (
        f"QPushButton {{"
        f"background:{BG_PANEL}; border:1px solid {BORDER}; border-bottom:none;"
        f"border-radius:6px 6px 0 0; padding:6px 6px 6px 12px;"
        f"font-size:12px; color:{TEXT_MUT}; min-width:80px; text-align:left;}}"
        f"QPushButton:hover{{background:{BG_HOVER}; color:{TEXT_SEC};}}"
    )
    _ACTIVE = (
        f"QPushButton {{"
        f"background:{BG_CARD}; border:1px solid {BORDER}; border-bottom:2px solid {BG_CARD};"
        f"border-top:2px solid {BORDER_ACC}; border-radius:6px 6px 0 0;"
        f"padding:6px 6px 6px 12px; font-size:12px; font-weight:bold;"
        f"color:{TEXT_PRI}; min-width:80px; text-align:left;}}"
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tabs = []
        self._active = -1
        self.setStyleSheet(f"background:{BG_PANEL};")
        self.setFixedHeight(44)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 8, 12, 0)
        self._layout.setSpacing(3)
        self._layout.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

        self._add_btn = QPushButton("＋")
        self._add_btn.setFixedSize(28, 28)
        self._add_btn.setToolTip("Добавить страницу")
        self._add_btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:1px dashed {BORDER_LT};"
            f"border-radius:6px;color:{TEXT_MUT};font-size:15px;}}"
            f"QPushButton:hover{{background:{BG_HOVER};border-color:{BORDER_ACC};color:{ACCENT};}}"
        )
        self._add_btn.clicked.connect(self.tab_added.emit)
        self._layout.addWidget(self._add_btn)

    def add_tab(self, name: str) -> int:
        idx = len(self._tabs)

        container = QWidget()
        container.setStyleSheet("background:transparent;")
        h = QHBoxLayout(container)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(2)

        btn = QPushButton(f"📄  {name}")
        btn.setStyleSheet(self._NORMAL)
        btn.clicked.connect(lambda _, i=idx: self._select(i))
        btn.mouseDoubleClickEvent = lambda e, i=idx: self._rename(i)
        h.addWidget(btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(16, 16)
        close_btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;color:{TEXT_MUT};font-size:10px;}}"
            f"QPushButton:hover{{color:{ACCENT_RED};}}"
        )
        close_btn.clicked.connect(lambda _, i=idx: self._close(i))
        h.addWidget(close_btn)

        self._tabs.append({'name': name, 'btn': btn, 'close_btn': close_btn, 'container': container})

        # Вставить перед кнопкой «+»
        self._layout.insertWidget(self._layout.count() - 1, container)

        if self._active < 0:
            self._select(0)

        return idx

    def rename_tab(self, idx: int, name: str):
        if 0 <= idx < len(self._tabs):
            self._tabs[idx]['name'] = name
            self._tabs[idx]['btn'].setText(f"📄  {name}")

    def remove_tab(self, idx: int):
        if 0 <= idx < len(self._tabs):
            tab = self._tabs.pop(idx)
            tab['container'].hide()
            tab['container'].deleteLater()
            self._rebuild_connections()
            new_active = min(self._active, len(self._tabs) - 1)
            self._active = -1
            if new_active >= 0:
                self._select(new_active)

    def current_index(self) -> int:
        return self._active

    def count(self) -> int:
        return len(self._tabs)

    def tab_name(self, idx: int) -> str:
        if 0 <= idx < len(self._tabs):
            return self._tabs[idx]['name']
        return ''

    def _select(self, idx: int):
        for i, tab in enumerate(self._tabs):
            tab['btn'].setStyleSheet(self._ACTIVE if i == idx else self._NORMAL)
        self._active = idx
        self.tab_selected.emit(idx)

    def _rename(self, idx: int):
        old = self._tabs[idx]['name']
        new, ok = QInputDialog.getText(self, "Переименовать страницу", "Новое название:", text=old)
        if ok and new.strip():
            self.rename_tab(idx, new.strip())
            self.tab_renamed.emit(idx, new.strip())

    def _close(self, idx: int):
        if len(self._tabs) <= 1:
            QMessageBox.information(self, "Нельзя удалить", "Нельзя удалить единственную страницу.")
            return
        self.tab_closed.emit(idx)

    def refresh_styles(self):
        """Перегенерирует все стили вкладок из текущей темы."""
        self.setStyleSheet(f"background:{_tm.BG_PANEL};")
        self._NORMAL = (
            f"QPushButton {{background:{_tm.BG_PANEL}; border:1px solid {_tm.BORDER};"
            f"border-bottom:none; border-radius:6px 6px 0 0; padding:6px 6px 6px 12px;"
            f"font-size:12px; color:{_tm.TEXT_MUT}; min-width:80px; text-align:left;}}"
            f"QPushButton:hover{{background:{_tm.BG_HOVER}; color:{_tm.TEXT_SEC};}}"
        )
        self._ACTIVE = (
            f"QPushButton {{background:{_tm.BG_CARD}; border:1px solid {_tm.BORDER};"
            f"border-bottom:2px solid {_tm.BG_CARD}; border-top:2px solid {_tm.BORDER_ACC};"
            f"border-radius:6px 6px 0 0; padding:6px 6px 6px 12px; font-size:12px;"
            f"font-weight:bold; color:{_tm.TEXT_PRI}; min-width:80px; text-align:left;}}"
        )
        self._add_btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:1px dashed {_tm.BORDER_LT};"
            f"border-radius:6px;color:{_tm.TEXT_MUT};font-size:15px;}}"
            f"QPushButton:hover{{background:{_tm.BG_HOVER};border-color:{_tm.BORDER_ACC};"
            f"color:{_tm.ACCENT};}}"
        )
        for i, tab in enumerate(self._tabs):
            tab['btn'].setStyleSheet(self._ACTIVE if i == self._active else self._NORMAL)
            tab['close_btn'].setStyleSheet(
                f"QPushButton{{background:transparent;border:none;"
                f"color:{_tm.TEXT_MUT};font-size:10px;}}"
                f"QPushButton:hover{{color:{_tm.ACCENT_RED};}}"
            )

    def _rebuild_connections(self):
        for i, tab in enumerate(self._tabs):
            btn, close_btn = tab['btn'], tab['close_btn']
            try:
                btn.clicked.disconnect()
                close_btn.clicked.disconnect()
            except RuntimeError:
                pass
            btn.clicked.connect(lambda _, i=i: self._select(i))
            btn.mouseDoubleClickEvent = lambda e, i=i: self._rename(i)
            close_btn.clicked.connect(lambda _, i=i: self._close(i))


# ─── Боковая панель — резюме дашборда ────────────────────────────────────────

class DashboardSummary(QFrame):
    """
    Боковая панель с обзором текущего дашборда:
    имя файла, список страниц с числом блоков, типы виджетов, загруженные датасеты.
    Внизу — кнопка «Добавить виджет».
    """

    add_widget_clicked = Signal()

    _TYPE_NAMES = {
        'chart':    '📈 График',
        'kpi':      '🔢 KPI',
        'table':    '📋 Таблица',
        'map':      '🗺 Карта',
        'text':     '📝 Текст',
        'image':    '🖼 Изображ.',
        'filter':   '🔍 Фильтр',
        'gauge':    '⊙ Датчик',
        'progress': '≡ Прогресс',
        'pivot':    '⊞ Сводная',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(210)
        self.setStyleSheet(
            f"QFrame {{background:{BG_PANEL}; border-right:1px solid {BORDER};}}"
        )
        self._init_ui()

    # ── Построение UI ──────────────────────────────────────────────────────────

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Шапка
        hdr_w = QWidget()
        hdr_w.setFixedHeight(40)
        hdr_w.setStyleSheet(f"background:{BG_DARK}; border-bottom:1px solid {BORDER};")
        hdr_lay = QHBoxLayout(hdr_w)
        hdr_lay.setContentsMargins(12, 0, 12, 0)
        hdr_lbl = QLabel("📋  Обзор")
        hdr_lbl.setStyleSheet(
            f"font-size:12px; font-weight:bold; color:{TEXT_PRI}; background:transparent; border:none;"
        )
        hdr_lay.addWidget(hdr_lbl)
        root.addWidget(hdr_w)

        # Контент
        content = QWidget()
        content.setStyleSheet("background:transparent;")
        self._lay = QVBoxLayout(content)
        self._lay.setContentsMargins(12, 12, 12, 8)
        self._lay.setSpacing(8)

        # Имя дашборда
        self._name_lbl = self._val("Новый дашборд")
        self._name_lbl.setStyleSheet(
            f"font-size:11px; font-weight:600; color:{ACCENT};"
            f" background:transparent; border:none;"
        )
        self._lay.addWidget(self._name_lbl)

        self._lay.addWidget(self._sep())

        # Страницы
        self._lay.addWidget(self._hdr("📄  Страницы"))
        self._pages_lbl = self._val("—")
        self._lay.addWidget(self._pages_lbl)

        self._lay.addWidget(self._sep())

        # Блоки (виджеты)
        self._lay.addWidget(self._hdr("🧩  Блоки"))
        self._widgets_lbl = self._val("—")
        self._lay.addWidget(self._widgets_lbl)

        self._lay.addWidget(self._sep())

        # Датасеты
        self._lay.addWidget(self._hdr("📊  Датасеты"))
        self._ds_lbl = self._val("Не загружены")
        self._lay.addWidget(self._ds_lbl)

        self._lay.addStretch()
        root.addWidget(content, 1)

        # Кнопка внизу
        footer = QWidget()
        footer.setFixedHeight(56)
        footer.setStyleSheet(f"background:{BG_DARK}; border-top:1px solid {BORDER};")
        foot_lay = QVBoxLayout(footer)
        foot_lay.setContentsMargins(10, 10, 10, 10)

        add_btn = QPushButton("＋  Добавить виджет")
        add_btn.setFixedHeight(34)
        add_btn.setStyleSheet(
            f"QPushButton{{background:{ACCENT_DARK};color:{TEXT_PRI};border:none;"
            f"border-radius:6px;font-size:12px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{ACCENT};color:#0F1A0F;}}"
        )
        add_btn.clicked.connect(self.add_widget_clicked.emit)
        foot_lay.addWidget(add_btn)
        root.addWidget(footer)

    # ── Вспомогательные виджеты ────────────────────────────────────────────────

    def _hdr(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size:10px; font-weight:600; color:{TEXT_SEC};"
            f" background:transparent; border:none; letter-spacing:0.5px;"
        )
        return lbl

    def _val(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size:11px; color:{TEXT_MUT}; background:transparent; border:none;"
        )
        lbl.setWordWrap(True)
        return lbl

    def _sep(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        f.setFixedHeight(1)
        f.setStyleSheet(f"background:{BORDER}; border:none;")
        return f

    # ── Обновление данных ─────────────────────────────────────────────────────

    def update_summary(
        self,
        dash_name: str,
        pages: list,          # [{'name': str, 'widget_count': int, 'widget_types': dict}]
        datasets: dict,       # {name: DataFrame}
    ):
        self._name_lbl.setText(dash_name)

        # Страницы
        if pages:
            parts = []
            for p in pages:
                cnt = p.get('widget_count', 0)
                note = f" · {cnt}" if cnt else " · пусто"
                parts.append(f"• {p['name']}{note}")
            self._pages_lbl.setText("\n".join(parts))
        else:
            self._pages_lbl.setText("—")

        # Блоки — итого + разбивка по типам
        total = sum(p.get('widget_count', 0) for p in pages)
        if total:
            type_acc: dict = {}
            for p in pages:
                for wtype, cnt in p.get('widget_types', {}).items():
                    type_acc[wtype] = type_acc.get(wtype, 0) + cnt
            lines = [f"Всего: {total}"]
            for wtype, cnt in sorted(type_acc.items(), key=lambda x: -x[1]):
                nm = self._TYPE_NAMES.get(wtype, wtype)
                lines.append(f"  {nm}: {cnt}")
            self._widgets_lbl.setText("\n".join(lines))
        else:
            self._widgets_lbl.setText("Нет блоков")

        # Датасеты
        if datasets:
            lines = []
            for name, df in list(datasets.items())[:6]:   # не более 6
                try:
                    lines.append(f"• {name}\n  {len(df)} стр., {len(df.columns)} кол.")
                except Exception:
                    lines.append(f"• {name}")
            if len(datasets) > 6:
                lines.append(f"  … ещё {len(datasets)-6}")
            self._ds_lbl.setText("\n".join(lines))
        else:
            self._ds_lbl.setText("Не загружены")


# ─── Главное окно ─────────────────────────────────────────────────────────────

class ConfiguratorWindow(QWidget, LoggerMixin):
    """Конструктор многостраничных дашбордов."""

    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.log.info("Инициализация ConfiguratorWindow")

        self._datasets: dict        = {}
        self._pages: list           = []   # list[DashboardGrid]
        self._current_save_path: str | None = None   # путь к текущему файлу
        self._has_unsaved_changes: bool = False
        self._toolbar_btns: list    = []   # list of (QPushButton, is_accent)

        self._init_ui()
        self._add_page("Страница 1")

        # BUG 3 FIX: apply the current theme when the window is first created,
        # so that opening the configurator after returning from the main menu
        # always uses the correct theme colours.
        self._refresh_theme_styles()

        self.log.info("ConfiguratorWindow инициализирован")

    # ─── Сборка UI ───────────────────────────────────────────────────────────

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_toolbar())

        body = QWidget()
        body.setStyleSheet(f"background:{BG_DARK};")
        self._body_widget = body
        body_h = QHBoxLayout(body)
        body_h.setContentsMargins(0, 0, 0, 0)
        body_h.setSpacing(0)

        # Боковая панель — резюме дашборда
        self._summary = DashboardSummary()
        self._summary.add_widget_clicked.connect(self._on_add_widget_clicked)
        body_h.addWidget(self._summary)

        # Правая часть
        right = QWidget()
        right.setStyleSheet("background:transparent;")
        right_v = QVBoxLayout(right)
        right_v.setContentsMargins(0, 0, 0, 0)
        right_v.setSpacing(0)

        self._tab_bar = PageTabBar()
        self._tab_bar.tab_selected.connect(self._on_tab_selected)
        self._tab_bar.tab_closed.connect(self._on_tab_closed)
        self._tab_bar.tab_added.connect(self._on_tab_added)
        self._tab_bar.tab_renamed.connect(self._on_tab_renamed)
        right_v.addWidget(self._tab_bar)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background:{BORDER};")
        sep.setFixedHeight(1)
        right_v.addWidget(sep)

        self._stack = QStackedWidget()
        right_v.addWidget(self._stack, 1)

        body_h.addWidget(right, 1)
        root.addWidget(body, 1)

    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(48)
        bar.setStyleSheet(f"background:{BG_PANEL}; border-bottom:1px solid {BORDER};")
        self._toolbar_bar = bar
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(6)

        self._make_btn(lay, "← Назад", self.go_back)
        self._sep(lay)
        self.save_btn = self._make_btn(lay, "💾 Сохранить", self.save_dashboard)
        self.save_btn.setEnabled(False)
        self._sep(lay)
        self._ds_btn = self._make_btn(lay, "📂 Загрузить данные", self._open_dataset_manager, accent=True)
        self._sep(lay)
        self._make_btn(lay, "🌐 HTML", self.export_html)
        self._make_btn(lay, "📋 Отчёт", self.export_report_action)
        self._make_btn(lay, "📷 Экспорт PNG", self.export_png)

        lay.addStretch()

        # ── Переключатель темы ───────────────────────────────────────────────
        theme_lbl = QLabel("Тема:")
        theme_lbl.setStyleSheet(f"color:{TEXT_MUT}; font-size:11px; padding-right:2px;")
        lay.addWidget(theme_lbl)
        self._theme_lbl = theme_lbl

        self._theme_combo = QComboBox()
        self._theme_combo.setFixedHeight(28)
        self._theme_combo.setFixedWidth(140)
        self._theme_combo.setStyleSheet(
            f"QComboBox{{background:{BG_CARD};color:{TEXT_PRI};"
            f"border:1px solid {BORDER};border-radius:5px;"
            f"padding:2px 8px;font-size:12px;min-height:0;}}"
            f"QComboBox:hover{{border-color:{BORDER_LT};}}"
            f"QComboBox::drop-down{{border:none;width:18px;}}"
            f"QComboBox QAbstractItemView{{background:{BG_PANEL};color:{TEXT_PRI};"
            f"border:1px solid {BORDER_LT};selection-background-color:{BG_ACTIVE};"
            f"selection-color:{ACCENT};}}"
        )
        for tid, tname in THEME_LIST:
            self._theme_combo.addItem(tname, tid)
        # BUG 3 FIX: initialise combo to the *current* active theme, not just index 0.
        # This ensures the combo reflects the actual theme after navigating back.
        cur_idx = next((i for i, (tid, _) in enumerate(THEME_LIST)
                        if tid == _tm.CURRENT_THEME_NAME), 0)
        self._theme_combo.setCurrentIndex(cur_idx)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        lay.addWidget(self._theme_combo)

        self._sep(lay)

        # Имя текущего дашборда
        self._current_name_lbl = QLabel("● Новый дашборд")
        self._current_name_lbl.setStyleSheet(
            f"color:{TEXT_MUT}; font-size:11px; padding-right:8px;"
        )
        lay.addWidget(self._current_name_lbl)

        self._sep(lay)

        self._info_label = QLabel("")
        self._info_label.setStyleSheet(f"color:{TEXT_MUT}; font-size:11px;")
        lay.addWidget(self._info_label)

        return bar

    def _make_btn(self, layout, text: str, slot, accent=False) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(32)
        if accent:
            btn.setStyleSheet(
                f"QPushButton{{background:{ACCENT_DARK};color:{TEXT_PRI};border:none;"
                f"border-radius:6px;padding:0 14px;font-size:12px;}}"
                f"QPushButton:hover{{background:{ACCENT};color:#0F1A0F;}}"
                f"QPushButton:disabled{{background:{BORDER};}}"
            )
        else:
            btn.setStyleSheet(
                f"QPushButton{{background:{BG_CARD};border:1px solid {BORDER};"
                f"border-radius:6px;padding:0 14px;font-size:12px;color:{TEXT_SEC};}}"
                f"QPushButton:hover{{background:{BG_HOVER};border-color:{BORDER_LT};color:{TEXT_PRI};}}"
                f"QPushButton:disabled{{color:{TEXT_MUT};}}"
            )
        btn.clicked.connect(slot)
        layout.addWidget(btn)
        self._toolbar_btns.append((btn, accent))
        return btn

    def _sep(self, layout):
        lbl = QLabel("|")
        lbl.setStyleSheet(f"color:{BORDER_LT}; font-size:16px; padding:0 2px;")
        layout.addWidget(lbl)

    # ─── Тема ─────────────────────────────────────────────────────────────────

    def _on_theme_changed(self, _index: int):
        """Вызывается при смене темы в combo-box."""
        name = self._theme_combo.currentData()
        if name and name != _tm.CURRENT_THEME_NAME:
            set_active_theme(name)
            self._refresh_theme_styles()

    def _refresh_theme_styles(self):
        """
        BUG 3 FIX: Перегенерирует inline-стили всех key-виджетов тулбара и окна.
        Now also syncs the theme combo-box to the *current* active theme so that
        returning from the main menu and re-opening the configurator shows the
        correct theme rather than reverting to the default appearance.
        """
        # Sync combo to current theme (in case theme changed externally or we just created the window)
        cur_idx = next((i for i in range(self._theme_combo.count())
                        if self._theme_combo.itemData(i) == _tm.CURRENT_THEME_NAME), -1)
        if cur_idx >= 0 and self._theme_combo.currentIndex() != cur_idx:
            self._theme_combo.blockSignals(True)
            self._theme_combo.setCurrentIndex(cur_idx)
            self._theme_combo.blockSignals(False)

        # Toolbar bar background
        self._toolbar_bar.setStyleSheet(
            f"background:{_tm.BG_PANEL}; border-bottom:1px solid {_tm.BORDER};"
        )
        # Body
        self._body_widget.setStyleSheet(f"background:{_tm.BG_DARK};")
        # Summary panel
        self._summary.setStyleSheet(
            f"QFrame {{background:{_tm.BG_PANEL}; border-right:1px solid {_tm.BORDER};}}"
        )
        # Theme label
        self._theme_lbl.setStyleSheet(f"color:{_tm.TEXT_MUT}; font-size:11px; padding-right:2px;")
        # Theme combo
        self._theme_combo.setStyleSheet(
            f"QComboBox{{background:{_tm.BG_CARD};color:{_tm.TEXT_PRI};"
            f"border:1px solid {_tm.BORDER};border-radius:5px;"
            f"padding:2px 8px;font-size:12px;min-height:0;}}"
            f"QComboBox:hover{{border-color:{_tm.BORDER_LT};}}"
            f"QComboBox::drop-down{{border:none;width:18px;}}"
            f"QComboBox QAbstractItemView{{background:{_tm.BG_PANEL};color:{_tm.TEXT_PRI};"
            f"border:1px solid {_tm.BORDER_LT};selection-background-color:{_tm.BG_ACTIVE};"
            f"selection-color:{_tm.ACCENT};}}"
        )
        # Toolbar buttons
        for btn, is_accent in self._toolbar_btns:
            if is_accent:
                btn.setStyleSheet(
                    f"QPushButton{{background:{_tm.ACCENT_DARK};color:{_tm.TEXT_PRI};border:none;"
                    f"border-radius:6px;padding:0 14px;font-size:12px;}}"
                    f"QPushButton:hover{{background:{_tm.ACCENT};color:#0F1A0F;}}"
                    f"QPushButton:disabled{{background:{_tm.BORDER};}}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton{{background:{_tm.BG_CARD};border:1px solid {_tm.BORDER};"
                    f"border-radius:6px;padding:0 14px;font-size:12px;color:{_tm.TEXT_SEC};}}"
                    f"QPushButton:hover{{background:{_tm.BG_HOVER};border-color:{_tm.BORDER_LT};"
                    f"color:{_tm.TEXT_PRI};}}"
                    f"QPushButton:disabled{{color:{_tm.TEXT_MUT};}}"
                )
        # Labels
        self._current_name_lbl.setStyleSheet(
            f"color:{_tm.TEXT_MUT}; font-size:11px; padding-right:8px;"
        )
        self._info_label.setStyleSheet(f"color:{_tm.TEXT_MUT}; font-size:11px;")
        # Tab bar
        self._tab_bar.refresh_styles()
        # Dashboard grids (canvas, splitters, cells)
        for grid in self._pages:
            grid.refresh_theme()

    # ─── Страницы ─────────────────────────────────────────────────────────────

    def _add_page(self, name: str = None) -> int:
        idx = len(self._pages)
        name = name or f"Страница {idx + 1}"

        grid = DashboardGrid(rows=2, cols=3)
        grid.widget_added.connect(self._on_widget_added)
        grid.widget_removed.connect(self._on_widget_removed)
        grid.grid_changed.connect(self._on_grid_changed)

        if self._datasets:
            grid.set_datasets(self._datasets)

        self._pages.append(grid)
        self._stack.addWidget(grid)
        self._tab_bar.add_tab(name)
        return idx

    def _on_tab_selected(self, idx: int):
        if 0 <= idx < len(self._pages):
            self._stack.setCurrentIndex(idx)
        self._update_info()

    def _on_tab_added(self):
        idx = self._add_page()
        self._tab_bar._select(idx)
        self.save_btn.setEnabled(True)

    def _on_tab_closed(self, idx: int):
        if 0 <= idx < len(self._pages):
            grid = self._pages.pop(idx)
            self._stack.removeWidget(grid)
            grid.deleteLater()
        self._tab_bar.remove_tab(idx)
        self._update_info()

    def _on_tab_renamed(self, idx: int, name: str):
        pass  # имя уже обновлено в tab_bar

    def _current_grid(self) -> DashboardGrid:
        idx = self._tab_bar.current_index()
        if 0 <= idx < len(self._pages):
            return self._pages[idx]
        return None

    # ─── Виджеты ─────────────────────────────────────────────────────────────

    def _on_widget_added(self, row, col, widget_type, settings):
        self.log.info(f"Виджет ({row},{col}): {widget_type}")
        self._has_unsaved_changes = True
        self.save_btn.setEnabled(True)
        self._update_current_name()
        self._update_info()
        self._refresh_summary()

    def _on_widget_removed(self, row, col):
        self.log.info(f"Удалён ({row},{col})")
        self._has_unsaved_changes = True
        self._update_current_name()
        self._update_info()
        self._refresh_summary()

    def _on_grid_changed(self):
        self._has_unsaved_changes = True
        self._update_current_name()
        self._update_info()
        self._refresh_summary()

    def _update_info(self):
        grid = self._current_grid()
        if not grid:
            return
        n = grid.get_widgets_count()
        page = self._tab_bar.tab_name(self._tab_bar.current_index())
        ds = f" · {len(self._datasets)} датасет{'ов' if len(self._datasets)!=1 else ''}" if self._datasets else ""
        self._info_label.setText(f"{page}  —  блоков: {n}  |  {grid.rows}×{grid.cols}{ds}")
        if hasattr(self, '_ds_btn'):
            self._ds_btn.setText(f"📂 Загрузить данные ({len(self._datasets)})" if self._datasets else "📂 Загрузить данные")

    # ─── Добавление виджета ──────────────────────────────────────────────────

    def _on_add_widget_clicked(self):
        """Открывает диалог создания виджета для первой свободной ячейки."""
        grid = self._current_grid()
        if not grid:
            return
        for row in range(grid.rows):
            for col in range(grid.cols):
                if grid.is_empty_at(row, col):
                    self._open_creation_dialog('', row, col)
                    return
        QMessageBox.information(
            self, "Нет места",
            "Все ячейки заняты.\nДобавьте строку или колонку кнопками внизу сетки."
        )

    # ─── Обновление резюме ───────────────────────────────────────────────────

    def _refresh_summary(self):
        """Собирает данные по всем страницам и обновляет панель обзора."""
        if not hasattr(self, '_summary'):
            return

        # Имя дашборда
        if self._current_save_path:
            dash_name = os.path.basename(self._current_save_path).replace('.json', '')
            if self._has_unsaved_changes:
                dash_name = "● " + dash_name
        else:
            dash_name = "Новый дашборд"

        # Данные по страницам
        pages_data = []
        for i, grid in enumerate(self._pages):
            ser = grid.serialize()
            widgets = ser.get('widgets', [])
            type_counter: dict = {}
            for w in widgets:
                wt = w.get('type', 'unknown')
                type_counter[wt] = type_counter.get(wt, 0) + 1
            pages_data.append({
                'name':         self._tab_bar.tab_name(i),
                'widget_count': len(widgets),
                'widget_types': type_counter,
            })

        self._summary.update_summary(dash_name, pages_data, self._datasets)

    def _open_creation_dialog(self, preset_type: str, row: int, col: int):
        dlg = WidgetCreationDialog(self, preset_type=preset_type, datasets=self._datasets)
        dlg.widget_created.connect(
            lambda wtype, settings: self._place_widget(row, col, wtype, settings)
        )
        dlg.exec()

    def _place_widget(self, row: int, col: int, widget_type: str, settings: dict):
        grid = self._current_grid()
        if not grid:
            return
        try:
            widget = DashboardWidgetFactory.create(widget_type, settings)
            widget.edit_requested.connect(
                lambda w=widget, t=widget_type, r=row, c=col: self._edit_widget(r, c, w, t)
            )
            if self._datasets:
                widget.set_datasets(self._datasets)
            grid.add_widget(widget, widget_type, row, col)
        except Exception as e:
            self.log.error(f"Ошибка создания виджета: {e}")
            # BUG 8 FIX: show error in a visible, properly styled message box
            QMessageBox.critical(self, "Ошибка создания виджета", str(e))

    def _edit_widget(self, row, col, widget, widget_type):
        dlg = WidgetCreationDialog(self, preset_type=widget_type, datasets=self._datasets)
        dlg.load_settings(widget_type, widget.settings())
        dlg.widget_created.connect(
            lambda nt, ns: self._update_widget(row, col, nt, ns)
        )
        dlg.exec()

    def _update_widget(self, row, col, widget_type, settings):
        grid = self._current_grid()
        if not grid:
            return
        try:
            grid.remove_widget(row, col)
            widget = DashboardWidgetFactory.create(widget_type, settings)
            widget.edit_requested.connect(
                lambda w=widget, t=widget_type, r=row, c=col: self._edit_widget(r, c, w, t)
            )
            if self._datasets:
                widget.set_datasets(self._datasets)
            grid.add_widget(widget, widget_type, row, col)
        except Exception as e:
            self.log.error(f"Ошибка обновления виджета: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))

    # ─── Загрузка данных ─────────────────────────────────────────────────────

    def load_data_file(self):
        """Загружает CSV или Excel-файл как датасет для дашборда."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Загрузить данные",
            os.path.expanduser('~'),
            "Таблицы (*.csv *.xlsx *.xls *.tsv);;CSV файлы (*.csv);;Excel (*.xlsx *.xls);;Все файлы (*)"
        )
        if not path:
            return
        try:
            import pandas as pd
            fname = os.path.splitext(os.path.basename(path))[0]
            ext   = os.path.splitext(path)[1].lower()
            if ext in ('.xlsx', '.xls'):
                df = pd.read_excel(path)
            elif ext == '.tsv':
                df = pd.read_csv(path, sep='\t', encoding='utf-8-sig')
            else:
                df = pd.read_csv(path, encoding='utf-8-sig')

            # Добавляем в датасеты под именем файла (без пути)
            name = fname
            counter = 1
            while name in self._datasets:
                name = f"{fname}_{counter}"
                counter += 1
            self._datasets[name] = df
            self._on_datasets_changed(self._datasets)
            self.log.info(f"Загружены данные: {name} ({len(df)} строк, {len(df.columns)} столбцов)")
            QMessageBox.information(
                self, "Данные загружены",
                f"Файл «{os.path.basename(path)}» загружен как датасет «{name}».\n"
                f"Строк: {len(df)}, столбцов: {len(df.columns)}"
            )
        except Exception as e:
            self.log.error(f"Ошибка загрузки данных: {e}")
            QMessageBox.critical(self, "Ошибка загрузки", str(e))

    # ─── Экспорт в PNG ────────────────────────────────────────────────────────

    def export_png(self):
        """Экспортирует каждую страницу дашборда в отдельный PNG-файл."""
        if not self._pages:
            QMessageBox.information(self, "Нет страниц", "Нечего экспортировать: страниц нет.")
            return
        tdir = QFileDialog.getExistingDirectory(
            self, "Выберите папку для PNG-файлов",
            os.path.expanduser('~')
        )
        if not tdir:
            return
        try:
            saved = []
            current_idx = self._tab_bar.current_index()

            for i, grid in enumerate(self._pages):
                name = self._tab_bar.tab_name(i) or f"страница_{i+1}"
                # Безопасное имя файла
                safe = "".join(c if (c.isalnum() or c in ' _-') else '_' for c in name).strip()
                filename = f"{i+1:02d}_{safe}.png"
                filepath = os.path.join(tdir, filename)

                # Рендерим виджет в QPixmap
                pix = grid.grab()
                if pix.save(filepath, "PNG"):
                    saved.append(filename)
                else:
                    raise IOError(f"Не удалось сохранить: {filepath}")

            # Возвращаем активную страницу
            self._tab_bar._select(current_idx)

            self.log.info(f"PNG экспортировано: {len(saved)} страниц → {tdir}")
            QMessageBox.information(
                self, "Экспорт завершён",
                f"Сохранено {len(saved)} PNG-файл{'а' if len(saved) in (2,3,4) else 'ов' if len(saved)!=1 else ''}:\n"
                + "\n".join(saved) +
                f"\n\nПапка: {tdir}"
            )
        except Exception as e:
            self.log.error(f"Ошибка экспорта PNG: {e}")
            QMessageBox.critical(self, "Ошибка экспорта", str(e))

    # ─── Датасеты ─────────────────────────────────────────────────────────────

    def _open_dataset_manager(self):
        dlg = DatasetManager(self._datasets, self)
        dlg.exec()
        self._on_datasets_changed(dlg.get_datasets())

    def _on_datasets_changed(self, datasets: dict):
        self._datasets = datasets
        for grid in self._pages:
            grid.set_datasets(datasets)
        self._update_info()
        self._refresh_summary()

    # ─── Сохранение / загрузка ───────────────────────────────────────────────

    def _templates_dir(self) -> str:
        """
        Возвращает папку для хранения дашбордов.
        Приоритет: %APPDATA%\\EcologyBI (работает при запуске от Admin),
        запасной вариант — ~/Documents/EcologyBI, затем папка templates/ рядом с проектом.
        """
        # Windows: %APPDATA%\EcologyBI
        appdata = os.environ.get('APPDATA', '')
        if appdata:
            path = os.path.join(appdata, 'EcologyBI')
            try:
                os.makedirs(path, exist_ok=True)
                return path
            except Exception:
                pass
        # Fallback: ~/Documents/EcologyBI
        docs = os.path.join(os.path.expanduser('~'), 'Documents', 'EcologyBI')
        try:
            os.makedirs(docs, exist_ok=True)
            return docs
        except Exception:
            pass
        # Last resort: project templates/
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')

    def save_dashboard(self):
        tdir = self._templates_dir()
        os.makedirs(tdir, exist_ok=True)
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить дашборд", tdir, "JSON (*.json)"
        )
        if not path:
            return
        self._save_to_path(path)

    def _save_to_path(self, path: str, silent: bool = False):
        """
        BUG 8 FIX: Wrapped entire save in try/except with a visible error dialog.
        Previously errors could be swallowed silently.  Now they always surface
        as a QMessageBox.critical() so the user knows the save failed.
        """
        try:
            pages_data = []
            for i, grid in enumerate(self._pages):
                pages_data.append({
                    'name':    self._tab_bar.tab_name(i),
                    'rows':    grid.rows,
                    'columns': grid.cols,
                    'widgets': grid.serialize().get('widgets', []),
                })
            data = {
                'version':    '2.0',
                'name':       os.path.basename(path).replace('.json', ''),
                'created_at': datetime.now().isoformat(),
                'pages':      pages_data,
                'theme':      _tm.CURRENT_THEME_NAME,
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self._current_save_path  = os.path.abspath(path)
            self._has_unsaved_changes = False
            self.save_btn.setEnabled(True)
            self._update_current_name()
            self._refresh_summary()

            # Регистрируем в папке templates/
            try:
                tdir = self._templates_dir()
                os.makedirs(tdir, exist_ok=True)
                abs_path = os.path.abspath(path)

                # .last_template — путь к последнему сохранённому
                with open(os.path.join(tdir, '.last_template'), 'w', encoding='utf-8') as f:
                    f.write(abs_path)

                # _manifest.json — список всех когда-либо сохранённых файлов
                manifest_path = os.path.join(tdir, '_manifest.json')
                manifest: list = []
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                    except Exception:
                        manifest = []
                if abs_path not in manifest:
                    manifest.append(abs_path)
                with open(manifest_path, 'w', encoding='utf-8') as f:
                    json.dump(manifest, f, ensure_ascii=False, indent=2)
            except Exception:
                pass  # не критично

            self.log.info(f"Дашборд сохранён: {path}")
            if not silent:
                QMessageBox.information(self, "Сохранено", f"Дашборд сохранён:\n{path}")
        except Exception as e:
            self.log.error(f"Ошибка сохранения: {e}")
            if not silent:
                # BUG 8 FIX: always show the error — never silently discard it
                QMessageBox.critical(
                    self, "Ошибка сохранения",
                    f"Не удалось сохранить дашборд:\n{path}\n\nПричина: {e}"
                )
            raise

    def export_html(self):
        """Экспортирует текущий дашборд в standalone HTML-файл."""
        pages_data = []
        for i, grid in enumerate(self._pages):
            ser = grid.serialize()
            pages_data.append({
                'name':      self._tab_bar.tab_name(i),
                'rows':      grid.rows,
                'columns':   grid.cols,
                'widgets':   ser.get('widgets', []),
                'row_sizes': ser.get('row_sizes', []),
                'col_sizes': ser.get('col_sizes', []),
            })
        if not any(p['widgets'] for p in pages_data):
            QMessageBox.warning(self, "Экспорт HTML", "Нет виджетов для экспорта.")
            return

        dashboard_name = getattr(self, '_current_save_path', None)
        default_name   = (
            os.path.splitext(os.path.basename(dashboard_name))[0]
            if dashboard_name else 'dashboard'
        )
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт HTML", f"{default_name}.html", "HTML (*.html)"
        )
        if not path:
            return

        data = {
            'version':    '2.0',
            'name':       os.path.splitext(os.path.basename(path))[0],
            'created_at': datetime.now().isoformat(),
            'pages':      pages_data,
            'theme':      _tm.CURRENT_THEME_NAME,
        }
        try:
            export_to_html(data, path, open_browser=True)
            self.log.info(f"HTML экспортирован: {path}")
            QMessageBox.information(
                self, "Готово",
                f"HTML сохранён:\n{path}\n\nОткрывается в браузере."
            )
        except Exception as e:
            self.log.error(f"Ошибка экспорта HTML: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))

    def export_report_action(self):
        """Открывает диалог параметров отчёта и генерирует HTML-отчёт."""
        pages_data = []
        for i, grid in enumerate(self._pages):
            pages_data.append({
                'name':    self._tab_bar.tab_name(i),
                'rows':    grid.rows,
                'columns': grid.cols,
                'widgets': grid.serialize().get('widgets', []),
            })
        if not any(p['widgets'] for p in pages_data):
            QMessageBox.warning(self, "Отчёт", "Нет виджетов для формирования отчёта.")
            return

        dlg = ReportDialog(self)
        if not dlg.exec():
            return
        params = dlg.get_params()

        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчёт", "report.html", "HTML (*.html)"
        )
        if not path:
            return

        data = {
            'version':    '2.0',
            'name':       os.path.splitext(os.path.basename(path))[0],
            'created_at': datetime.now().isoformat(),
            'pages':      pages_data,
        }
        try:
            export_report(data, path, open_browser=True, **params)
            self.log.info(f"Отчёт сформирован: {path}")
            QMessageBox.information(
                self, "Готово",
                f"Отчёт сохранён:\n{path}\n\nОткрывается в браузере.\n"
                "Для PDF нажмите «Печать / PDF» на странице."
            )
        except Exception as e:
            self.log.error(f"Ошибка генерации отчёта: {e}")
            QMessageBox.critical(self, "Ошибка", str(e))

    def load_dashboard(self):
        path, _ = QFileDialog.getOpenFileName(self, "Загрузить дашборд", "", "JSON (*.json)")
        if not path:
            return
        self.load_dashboard_from_path(path)

    def load_dashboard_from_path(self, path: str):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Автосохраняем текущий (если путь другой)
            abs_new = os.path.abspath(path)
            if self._current_save_path and os.path.abspath(self._current_save_path) != abs_new:
                if self._has_unsaved_changes:
                    try:
                        self._save_to_path(self._current_save_path, silent=True)
                    except Exception:
                        pass

            # Удаляем все страницы
            count = self._tab_bar.count()
            for _ in range(count):
                if self._pages:
                    grid = self._pages.pop(0)
                    self._stack.removeWidget(grid)
                    grid.deleteLater()
            for _ in range(count):
                if self._tab_bar.count() > 0:
                    self._tab_bar.remove_tab(0)

            # Совместимость с форматом v1
            pages = data.get('pages')
            if not pages:
                pages = [{
                    'name':    data.get('name', 'Страница 1'),
                    'rows':    data.get('rows', 2),
                    'columns': data.get('columns', 3),
                    'widgets': data.get('widgets', []),
                }]

            for pd_ in pages:
                idx = self._add_page(pd_.get('name', 'Страница'))
                grid = self._pages[idx]
                while grid.rows < pd_.get('rows', 2):
                    grid.add_row()
                while grid.cols < pd_.get('columns', 3):
                    grid.add_column()

                error_count = 0
                for wd in pd_.get('widgets', []):
                    row, col = wd.get('row', 0), wd.get('col', 0)
                    wtype = wd.get('type', '')
                    settings = wd.get('settings', {})
                    if wtype:
                        try:
                            widget = DashboardWidgetFactory.create(wtype, settings)
                            widget.edit_requested.connect(
                                lambda w=widget, t=wtype, r=row, c=col: self._edit_widget(r, c, w, t)
                            )
                            if self._datasets:
                                widget.set_datasets(self._datasets)
                            grid.add_widget(widget, wtype, row, col,
                                            wd.get('row_span', 1), wd.get('col_span', 1))
                        except Exception as e:
                            self.log.error(f"Ошибка загрузки виджета {wtype}: {e}")
                            error_count += 1

            if self._tab_bar.count() > 0:
                self._tab_bar._select(0)

            self._current_save_path  = os.path.abspath(path)
            self._has_unsaved_changes = False
            self.save_btn.setEnabled(True)
            self._update_current_name()
            self._update_info()
            self._refresh_summary()

            # Восстанавливаем тему из файла
            saved_theme = data.get('theme', '')
            if saved_theme and saved_theme != _tm.CURRENT_THEME_NAME:
                set_active_theme(saved_theme)
                self._refresh_theme_styles()
                # Синхронизируем combo-box
                idx = next((i for i in range(self._theme_combo.count())
                            if self._theme_combo.itemData(i) == saved_theme), -1)
                if idx >= 0:
                    self._theme_combo.blockSignals(True)
                    self._theme_combo.setCurrentIndex(idx)
                    self._theme_combo.blockSignals(False)

            msg = f"«{data.get('name','Без названия')}» — страниц: {len(pages)}"
            if error_count:
                msg += f"\n⚠ Не удалось загрузить виджетов: {error_count}"
            QMessageBox.information(self, "Загружено", msg)

        except Exception as e:
            # BUG 8 FIX: always show load errors in a visible dialog
            self.log.error(f"Ошибка загрузки дашборда: {e}")
            QMessageBox.critical(self, "Ошибка загрузки", str(e))

    # ─── Автосохранение и переключение ────────────────────────────────────────

    def auto_save(self) -> bool:
        """
        Тихо сохраняет текущий дашборд если известен путь.
        Возвращает True если сохранено или сохранять нечего.
        """
        if not self._has_unsaved_changes:
            return True
        if self._current_save_path:
            try:
                self._save_to_path(self._current_save_path, silent=True)
                self.log.info(f"Автосохранение: {self._current_save_path}")
                return True
            except Exception as e:
                self.log.error(f"Автосохранение не удалось: {e}")
                return False
        # Путь неизвестен — спросить
        reply = QMessageBox.question(
            self, "Сохранить дашборд?",
            "Текущий дашборд не сохранён. Сохранить перед переключением?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
        )
        if reply == QMessageBox.Save:
            self.save_dashboard()
            return True
        elif reply == QMessageBox.Discard:
            return True
        return False  # Cancel

    def _update_current_name(self):
        if self._current_save_path:
            base = os.path.basename(self._current_save_path).replace('.json', '')
            marker = '●' if self._has_unsaved_changes else '◉'
            self._current_name_lbl.setText(f"{marker} {base}")
            self._current_name_lbl.setStyleSheet(
                f"color:{'#fbbf24' if self._has_unsaved_changes else _tm.ACCENT};"
                f" font-size:11px; padding-right:8px;"
            )
        else:
            marker = '●' if self._has_unsaved_changes else '○'
            self._current_name_lbl.setText(f"{marker} Новый дашборд")
            self._current_name_lbl.setStyleSheet(
                f"color:{_tm.TEXT_MUT}; font-size:11px; padding-right:8px;"
            )

    def _open_switcher(self):
        """Показывает список сохранённых дашбордов для быстрого переключения."""
        tdir = self._templates_dir()
        files = []
        # Сканируем папку
        try:
            for f in sorted(os.listdir(tdir)):
                if f.endswith('.json') and not f.startswith(('.', '_')):
                    files.append(os.path.join(tdir, f))
        except Exception:
            pass
        # Добавляем из манифеста
        manifest_path = os.path.join(tdir, '_manifest.json')
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    for p in json.load(f):
                        if p not in files and os.path.exists(p):
                            files.append(p)
            except Exception:
                pass

        if not files:
            QMessageBox.information(self, "Нет дашбордов",
                "Сохранённых дашбордов не найдено.\nСохраните текущий через «💾 Сохранить».")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Открыть дашборд")
        dlg.setMinimumWidth(480)
        dlg.setStyleSheet(
            f"QDialog{{background:{_tm.BG_DARK};color:{_tm.TEXT_PRI};}}"
            f"QLabel{{color:{_tm.TEXT_SEC};background:transparent;}}"
        )
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        lbl = QLabel("Выберите дашборд:")
        lbl.setStyleSheet(f"font-size:12px;font-weight:600;color:{_tm.TEXT_PRI};")
        lay.addWidget(lbl)

        lst = QListWidget()
        lst.setStyleSheet(
            f"QListWidget{{background:{_tm.BG_CARD};border:1px solid {_tm.BORDER};"
            f"border-radius:5px;color:{_tm.TEXT_PRI};font-size:12px;outline:none;}}"
            f"QListWidget::item{{padding:8px 10px;border-bottom:1px solid {_tm.BG_PANEL};}}"
            f"QListWidget::item:selected{{background:{_tm.BG_ACTIVE};color:{_tm.ACCENT};}}"
            f"QListWidget::item:hover{{background:{_tm.BG_HOVER};}}"
        )
        for path in files:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                name  = data.get('name', os.path.basename(path))
                pages = len(data.get('pages', []))
                ts    = data.get('created_at', '')[:10]
                label = f"📊  {name}   ({pages} стр.)   {ts}"
            except Exception:
                label = f"📄  {os.path.basename(path)}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, path)
            # Отметим текущий
            if os.path.abspath(path) == (self._current_save_path and os.path.abspath(self._current_save_path)):
                item.setForeground(QColor(_tm.ACCENT))
                item.setText("▶ " + label)
            lst.addItem(item)

        lst.setMinimumHeight(200)
        lay.addWidget(lst)

        hint = QLabel("Двойной клик или «Открыть» — переключить. Текущий будет сохранён автоматически.")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"font-size:10px;color:{_tm.TEXT_MUT};")
        lay.addWidget(hint)

        btns = QDialogButtonBox()
        open_btn = btns.addButton("📂 Открыть", QDialogButtonBox.AcceptRole)
        new_btn  = btns.addButton("＋ Новый", QDialogButtonBox.ResetRole)
        btns.addButton("Отмена", QDialogButtonBox.RejectRole)
        btns.rejected.connect(dlg.reject)
        btns.accepted.connect(dlg.accept)
        open_btn.setStyleSheet(
            f"QPushButton{{background:{_tm.ACCENT_DARK};color:{_tm.TEXT_PRI};border:none;"
            f"border-radius:5px;padding:6px 16px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{_tm.ACCENT};}}"
        )

        def _do_new():
            dlg.done(2)

        new_btn.clicked.connect(_do_new)
        new_btn.setStyleSheet(
            f"QPushButton{{background:{_tm.BG_CARD};border:1px solid {_tm.BORDER};"
            f"border-radius:5px;padding:6px 14px;color:{_tm.TEXT_SEC};}}"
            f"QPushButton:hover{{border-color:{_tm.BORDER_LT};color:{_tm.TEXT_PRI};}}"
        )
        lay.addWidget(btns)

        lst.itemDoubleClicked.connect(lambda _: dlg.accept())

        result = dlg.exec()
        if result == 1:  # Accept → открыть выбранный
            sel = lst.currentItem()
            if sel:
                path = sel.data(Qt.UserRole)
                if path and os.path.abspath(path) != (
                    self._current_save_path and os.path.abspath(self._current_save_path)
                ):
                    if not self.auto_save():
                        return  # пользователь отменил
                    self.load_dashboard_from_path(path)
        elif result == 2:  # Новый
            if not self.auto_save():
                return
            self._new_dashboard()

    def _new_dashboard(self):
        """Создаёт пустой новый дашборд."""
        # Очищаем все страницы
        count = self._tab_bar.count()
        for _ in range(count):
            if self._pages:
                grid = self._pages.pop(0)
                self._stack.removeWidget(grid)
                grid.deleteLater()
        for _ in range(count):
            if self._tab_bar.count() > 0:
                self._tab_bar.remove_tab(0)
        self._current_save_path = None
        self._has_unsaved_changes = False
        self._datasets = {}
        self._add_page("Страница 1")
        self.save_btn.setEnabled(False)
        self._update_current_name()
        self._update_info()
        self._refresh_summary()

    # ─── Навигация ────────────────────────────────────────────────────────────

    def go_back(self):
        self.log.info("Назад")
        self.auto_save()   # тихо сохраняем если есть путь
        self.back_clicked.emit()

    def showEvent(self, event):
        """
        BUG 3 FIX: Re-apply the current theme every time the window becomes visible.
        This handles the case where the user navigated to the main menu (which may
        have reset theme state) and then returned to the configurator.
        """
        super().showEvent(event)
        self._refresh_theme_styles()
