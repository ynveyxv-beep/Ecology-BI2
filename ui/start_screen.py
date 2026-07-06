# ui/start_screen.py
"""
Стартовый экран Ecology-BI — тёмная природная тема.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QListWidget, QListWidgetItem, QMessageBox, QMenu
)
import os
import json

from ui.theme import (
    BG_DEEP, BG_DARK, BG_PANEL, BG_CARD, BG_HOVER, BG_ACTIVE,
    BORDER, BORDER_LT, BORDER_ACC,
    TEXT_PRI, TEXT_SEC, TEXT_MUT,
    ACCENT, ACCENT_DARK, ACCENT_RED, ACCENT_GOLD,
    VOLGA_DARK, VOLGA_MID, VOLGA_LIGHT,
    RADIUS, RADIUS_SM, RADIUS_LG,
    scrollbar_style
)


class StartScreen(QWidget):
    """Стартовый экран с выбором шаблонов."""

    mode_selected     = Signal(str)       # 'eco' | 'configurator'
    template_selected = Signal(str, str)  # 'load_template', path

    def __init__(self):
        super().__init__()
        self.templates_dir = self._templates_dir_abs()
        os.makedirs(self.templates_dir, exist_ok=True)
        # Загружаем закреплённый дашборд ДО построения UI
        self._pinned_static_path: str | None = self._load_pinned_static()
        self._init_ui()
        self.load_saved_templates()
        # Обновляем карточку с учётом закреплённого
        self._update_static_card()

    # ─── UI ──────────────────────────────────────────────────────────────────

    def _init_ui(self):
        self.setStyleSheet(f"background:{BG_DEEP};")

        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ─── Шапка ───────────────────────────────────────────────────────────
        header = QWidget()
        header.setStyleSheet(
            f"background:{BG_PANEL}; border-bottom:1px solid {BORDER};"
        )
        hdr_lay = QVBoxLayout(header)
        hdr_lay.setContentsMargins(40, 32, 40, 28)
        hdr_lay.setSpacing(8)

        title = QLabel("🌿  Ecology-BI")
        title.setStyleSheet(
            f"font-size:32px; font-weight:bold; color:{TEXT_PRI}; background:transparent;"
        )
        title.setAlignment(Qt.AlignCenter)
        hdr_lay.addWidget(title)

        subtitle = QLabel(
            "Система экологического мониторинга и конструктор аналитических дашбордов\n"
            "Нижегородский регион · Анализ данных · Визуализация"
        )
        subtitle.setStyleSheet(
            f"font-size:13px; color:{TEXT_MUT}; background:transparent;"
        )
        subtitle.setAlignment(Qt.AlignCenter)
        hdr_lay.addWidget(subtitle)

        root.addWidget(header)

        # ─── Основной контент ─────────────────────────────────────────────
        content = QWidget()
        content.setStyleSheet(f"background:{BG_DARK};")
        content_lay = QHBoxLayout(content)
        content_lay.setContentsMargins(40, 32, 40, 32)
        content_lay.setSpacing(24)

        content_lay.addWidget(self._create_eco_card(), 1)
        content_lay.addWidget(self._create_tools_card(), 1)

        root.addWidget(content, 1)

        # ─── Подвал ───────────────────────────────────────────────────────
        footer = QWidget()
        footer.setStyleSheet(
            f"background:{BG_PANEL}; border-top:1px solid {BORDER};"
        )
        ftr_lay = QHBoxLayout(footer)
        ftr_lay.setContentsMargins(40, 10, 40, 10)

        ver = QLabel("Ecology-BI v2.0  ·  Нижний Новгород")
        ver.setStyleSheet(f"font-size:10px; color:{TEXT_MUT}; background:transparent;")
        ftr_lay.addWidget(ver)
        ftr_lay.addStretch()

        nature = QLabel("🌲 Волга · Природа · Экология")
        nature.setStyleSheet(f"font-size:10px; color:{TEXT_MUT}; background:transparent;")
        ftr_lay.addWidget(nature)

        root.addWidget(footer)

    # ─── Карточки ────────────────────────────────────────────────────────────

    def _create_eco_card(self) -> QFrame:
        """Левая карточка — статический дашборд (по умолчанию Экологический мониторинг)."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background:{BG_CARD};
                border:2px solid {VOLGA_DARK};
                border-radius:6px;
            }}
            QFrame:hover {{
                border-color:{VOLGA_MID};
            }}
        """)
        card.setMinimumHeight(380)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(28, 12, 12, 24)
        lay.setSpacing(14)

        # ─── Верхняя строка: пусто + кнопка ⋯ ───────────────────────────
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(4)
        top_row.addStretch()

        dots_btn = QPushButton("⋯")
        dots_btn.setFixedSize(28, 28)
        dots_btn.setToolTip("Выбрать другой дашборд")
        dots_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_MUT};
                border: 1px solid transparent;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                padding-bottom: 4px;
            }}
            QPushButton:hover {{
                background: {BG_HOVER};
                border-color: {BORDER};
                color: {TEXT_PRI};
            }}
            QPushButton:pressed {{
                background: {BG_ACTIVE};
            }}
        """)
        dots_btn.clicked.connect(self._show_static_menu)
        top_row.addWidget(dots_btn)
        lay.addLayout(top_row)

        # ─── Иконка ──────────────────────────────────────────────────────
        self._static_icon_lbl = QLabel("🌿")
        self._static_icon_lbl.setStyleSheet(
            f"font-size:52px; background:transparent; border:none;"
        )
        self._static_icon_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._static_icon_lbl)

        # ─── Заголовок ───────────────────────────────────────────────────
        self._static_title_lbl = QLabel("Экологический мониторинг")
        self._static_title_lbl.setStyleSheet(
            f"font-size:20px; font-weight:bold; color:{VOLGA_LIGHT}; background:transparent; border:none;"
        )
        self._static_title_lbl.setAlignment(Qt.AlignCenter)
        self._static_title_lbl.setWordWrap(True)
        lay.addWidget(self._static_title_lbl)

        # ─── Описание ────────────────────────────────────────────────────
        self._static_desc_lbl = QLabel(
            "Готовый дашборд с KPI, временным рядом,\n"
            "категориями, географией и аналитикой\n"
            "экологической обстановки региона"
        )
        self._static_desc_lbl.setStyleSheet(
            f"font-size:12px; color:{TEXT_MUT}; background:transparent; border:none; line-height:1.5;"
        )
        self._static_desc_lbl.setAlignment(Qt.AlignCenter)
        self._static_desc_lbl.setWordWrap(True)
        lay.addWidget(self._static_desc_lbl)

        # ─── Теги ────────────────────────────────────────────────────────
        self._static_tags_row = QHBoxLayout()
        self._static_tags_row.setSpacing(6)
        self._static_tags_row.setAlignment(Qt.AlignCenter)
        for tag_text in ["KPI", "Карта", "Временной ряд", "Анализ"]:
            tag = QLabel(tag_text)
            tag.setStyleSheet(
                f"background:{VOLGA_DARK}; color:{VOLGA_LIGHT}; font-size:10px; font-weight:600;"
                f" border-radius:4px; padding:3px 8px; border:none;"
            )
            self._static_tags_row.addWidget(tag)
        lay.addLayout(self._static_tags_row)

        lay.addStretch()

        # ─── Кнопка открыть ──────────────────────────────────────────────
        self._static_open_btn = QPushButton("🚀  Открыть мониторинг")
        self._static_open_btn.setFixedHeight(44)
        self._static_open_btn.setStyleSheet(
            f"QPushButton{{background:{VOLGA_DARK};color:{VOLGA_LIGHT};border:none;"
            f"border-radius:6px;font-size:14px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{VOLGA_MID};color:white;}}"
        )
        self._static_open_btn.clicked.connect(self._open_static_dashboard)
        lay.addWidget(self._static_open_btn)

        return card

    def _create_tools_card(self) -> QFrame:
        """Правая карточка — Конструктор дашбордов."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background:{BG_CARD};
                border:2px solid {BORDER};
                border-radius:6px;
            }}
        """)
        card.setMinimumHeight(380)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(24, 24, 24, 20)
        lay.setSpacing(14)

        # Заголовок карточки
        card_title = QLabel("🛠️  Конструктор дашбордов")
        card_title.setStyleSheet(
            f"font-size:17px; font-weight:bold; color:{TEXT_PRI}; background:transparent; border:none;"
        )
        lay.addWidget(card_title)

        # ─── 1. Новый дашборд ─────────────────────────────────────────────
        new_section = self._section_widget(
            "🛠️  Новый дашборд",
            "Создайте дашборд с нуля — перетащите блоки на холст",
            "Открыть", self._open_configurator,
            accent=True
        )
        lay.addWidget(new_section)

        # ─── 2. Последний сохранённый ─────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background:{BORDER}; border:none;")
        sep.setFixedHeight(1)
        lay.addWidget(sep)

        last_hdr = QLabel("💾  Последний сохранённый")
        last_hdr.setStyleSheet(
            f"font-size:12px; font-weight:600; color:{TEXT_SEC}; background:transparent; border:none;"
        )
        lay.addWidget(last_hdr)

        last_row = QWidget()
        last_row.setStyleSheet(
            f"QWidget{{background:{BG_HOVER};border-radius:6px;border:1px solid {BORDER_LT};}}"
        )
        last_row_lay = QHBoxLayout(last_row)
        last_row_lay.setContentsMargins(12, 8, 8, 8)
        last_row_lay.setSpacing(8)

        self.last_template_name = QLabel("—")
        self.last_template_name.setStyleSheet(
            f"font-size:12px; color:{TEXT_MUT}; background:transparent; border:none;"
        )
        last_row_lay.addWidget(self.last_template_name, 1)

        last_btn = QPushButton("📂 Открыть")
        last_btn.setFixedHeight(30)
        last_btn.setStyleSheet(
            f"QPushButton{{background:{ACCENT_DARK};color:{TEXT_PRI};border:none;"
            f"border-radius:6px;padding:0 12px;font-size:11px;}}"
            f"QPushButton:hover{{background:{ACCENT};color:#0F1A0F;}}"
            f"QPushButton:disabled{{background:{BORDER};color:{TEXT_MUT};}}"
        )
        last_btn.clicked.connect(self._open_last_template)
        self._last_btn = last_btn
        last_row_lay.addWidget(last_btn)

        lay.addWidget(last_row)

        # ─── 3. Сохранённые дашборды ──────────────────────────────────────
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"background:{BORDER}; border:none;")
        sep2.setFixedHeight(1)
        lay.addWidget(sep2)

        saved_hdr = QHBoxLayout()
        saved_lbl = QLabel("📂  Сохранённые дашборды")
        saved_lbl.setStyleSheet(
            f"font-size:12px; font-weight:600; color:{TEXT_SEC}; background:transparent; border:none;"
        )
        saved_hdr.addWidget(saved_lbl)
        saved_hdr.addStretch()

        refresh_btn = QPushButton("↺")
        refresh_btn.setFixedSize(24, 24)
        refresh_btn.setToolTip("Обновить список")
        refresh_btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:1px solid {BORDER};"
            f"border-radius:5px;color:{TEXT_MUT};font-size:13px;}}"
            f"QPushButton:hover{{border-color:{BORDER_ACC};color:{ACCENT};}}"
        )
        refresh_btn.clicked.connect(self.load_saved_templates)
        saved_hdr.addWidget(refresh_btn)
        lay.addLayout(saved_hdr)

        self.templates_list = QListWidget()
        self.templates_list.setStyleSheet(
            f"QListWidget{{background:{BG_DARK};border:1px solid {BORDER};"
            f"border-radius:6px;padding:4px;outline:none;}}"
            f"QListWidget::item{{padding:6px 8px;border-radius:4px;"
            f"color:{TEXT_SEC};font-size:12px;}}"
            f"QListWidget::item:hover{{background:{BG_HOVER};color:{TEXT_PRI};}}"
            f"QListWidget::item:selected{{background:{BG_ACTIVE};color:{ACCENT};}}"
            + scrollbar_style()
        )
        self.templates_list.setMaximumHeight(110)
        self.templates_list.itemDoubleClicked.connect(self._load_selected_template)
        lay.addWidget(self.templates_list, 1)

        self._load_last_template_info()
        return card

    def _section_widget(self, title: str, desc: str, btn_text: str,
                        callback, accent=False) -> QWidget:
        w = QWidget()
        w.setStyleSheet(
            f"QWidget{{background:{BG_HOVER};border-radius:6px;border:1px solid {BORDER_LT};}}"
            f"QWidget:hover{{border-color:{BORDER_ACC};}}"
        )
        h = QHBoxLayout(w)
        h.setContentsMargins(12, 10, 10, 10)
        h.setSpacing(10)

        info = QVBoxLayout()
        info.setSpacing(3)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"font-size:13px; font-weight:bold; color:{TEXT_PRI}; background:transparent; border:none;"
        )
        info.addWidget(title_lbl)

        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(
            f"font-size:11px; color:{TEXT_MUT}; background:transparent; border:none;"
        )
        desc_lbl.setWordWrap(True)
        info.addWidget(desc_lbl)

        h.addLayout(info, 1)

        btn = QPushButton(btn_text)
        btn.setFixedHeight(34)
        if accent:
            btn.setStyleSheet(
                f"QPushButton{{background:{ACCENT_DARK};color:{TEXT_PRI};border:none;"
                f"border-radius:6px;padding:0 16px;font-size:12px;font-weight:bold;}}"
                f"QPushButton:hover{{background:{ACCENT};color:#0F1A0F;}}"
            )
        else:
            btn.setStyleSheet(
                f"QPushButton{{background:{BG_CARD};border:1px solid {BORDER};"
                f"border-radius:6px;padding:0 14px;font-size:12px;color:{TEXT_SEC};}}"
                f"QPushButton:hover{{background:{BG_ACTIVE};border-color:{BORDER_LT};color:{TEXT_PRI};}}"
            )
        btn.clicked.connect(callback)
        h.addWidget(btn)

        return w

    # ─── Статическая карточка — меню и закрепление ───────────────────────────

    def _show_static_menu(self):
        """Показывает меню выбора дашборда для статической карточки."""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {BG_PANEL};
                border: 1px solid {BORDER_LT};
                border-radius: 6px;
                padding: 4px;
                color: {TEXT_PRI};
                font-size: 12px;
            }}
            QMenu::item {{
                padding: 7px 14px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background: {BG_ACTIVE};
                color: {ACCENT};
            }}
            QMenu::separator {{
                height: 1px;
                background: {BORDER};
                margin: 4px 8px;
            }}
        """)

        # Заголовок (не кликабельный)
        title_action = QAction("Закрепить дашборд:", self)
        title_action.setEnabled(False)
        menu.addAction(title_action)
        menu.addSeparator()

        # Список всех сохранённых дашбордов
        dashboards = self._collect_all_dashboards()

        if dashboards:
            for name, path in dashboards:
                is_pinned = (
                    self._pinned_static_path is not None
                    and os.path.abspath(path) == os.path.abspath(self._pinned_static_path)
                )
                icon = "✅" if is_pinned else "📊"
                action = QAction(f"{icon}  {name}", self)
                action.triggered.connect(
                    lambda checked=False, p=path: self._pin_static_dashboard(p)
                )
                menu.addAction(action)
        else:
            no_action = QAction("Нет сохранённых дашбордов", self)
            no_action.setEnabled(False)
            menu.addAction(no_action)

        # Сброс на экомониторинг
        if self._pinned_static_path is not None:
            menu.addSeparator()
            reset_action = QAction("🌿  Вернуть экомониторинг", self)
            reset_action.triggered.connect(lambda: self._pin_static_dashboard(None))
            menu.addAction(reset_action)

        # Показываем у кнопки ⋯
        btn = self.sender()
        if btn:
            menu.exec(btn.mapToGlobal(btn.rect().bottomRight()))
        else:
            menu.exec(self.mapToGlobal(self.rect().topRight()))

    def _collect_all_dashboards(self) -> list[tuple[str, str]]:
        """Возвращает список (имя, путь) всех сохранённых дашбордов."""
        result = []
        seen: set = set()

        tdir = self._templates_dir_abs()
        legacy_dir = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
        )
        scan_dirs = list({tdir, legacy_dir})

        for d in scan_dirs:
            try:
                for file in sorted(os.listdir(d)):
                    if not file.endswith('.json') or file.startswith('.') or file.startswith('_'):
                        continue
                    abs_path = os.path.abspath(os.path.join(d, file))
                    if abs_path in seen:
                        continue
                    seen.add(abs_path)
                    try:
                        with open(abs_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        name = data.get('name', file.replace('.json', ''))
                    except Exception:
                        name = file.replace('.json', '')
                    result.append((name, abs_path))
            except Exception:
                pass

        return result

    def _pin_static_dashboard(self, path: str | None):
        """Закрепляет дашборд на статической карточке и сохраняет выбор."""
        self._pinned_static_path = path
        # Сохраняем на диск
        pf = os.path.join(self._templates_dir_abs(), '.pinned_static')
        if path:
            try:
                with open(pf, 'w', encoding='utf-8') as f:
                    f.write(os.path.abspath(path))
            except Exception:
                pass
        else:
            try:
                if os.path.exists(pf):
                    os.remove(pf)
            except Exception:
                pass
        self._update_static_card()

    def _update_static_card(self):
        """Обновляет содержимое левой карточки: либо закреплённый дашборд, либо экомониторинг."""
        if not hasattr(self, '_static_icon_lbl'):
            return  # UI ещё не построен

        if self._pinned_static_path and os.path.exists(self._pinned_static_path):
            # ─── Закреплённый дашборд ─────────────────────────────────
            try:
                with open(self._pinned_static_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                name  = data.get('name', os.path.basename(self._pinned_static_path))
                pages = len(data.get('pages', []))
            except Exception:
                name  = os.path.basename(self._pinned_static_path)
                pages = 0

            self._static_icon_lbl.setText('📊')
            self._static_title_lbl.setText(name)
            self._static_title_lbl.setStyleSheet(
                f"font-size:20px; font-weight:bold; color:{ACCENT};"
                f" background:transparent; border:none;"
            )

            pages_str = f"{pages} стр." if pages else ""
            self._static_desc_lbl.setText(
                f"Закреплённый дашборд{' · ' + pages_str if pages_str else ''}\n"
                f"Нажмите «Открыть», чтобы запустить.\n"
                f"Для смены дашборда нажмите ⋯"
            )

            # Скрываем теги — показываем путь
            self._clear_static_tags()
            file_tag = QLabel(f"📁 {os.path.basename(self._pinned_static_path)}")
            file_tag.setStyleSheet(
                f"background:{ACCENT_DARK}; color:{ACCENT}; font-size:10px; font-weight:600;"
                f" border-radius:4px; padding:3px 8px; border:none;"
            )
            self._static_tags_row.addWidget(file_tag)
            self._static_tags_row.setAlignment(Qt.AlignCenter)

            self._static_open_btn.setText('📂  Открыть дашборд')
            self._static_open_btn.setStyleSheet(
                f"QPushButton{{background:{ACCENT_DARK};color:{ACCENT};border:none;"
                f"border-radius:6px;font-size:14px;font-weight:bold;}}"
                f"QPushButton:hover{{background:{ACCENT};color:#0F1A0F;}}"
            )
        else:
            # ─── Экологический мониторинг (по умолчанию) ──────────────
            self._pinned_static_path = None
            self._static_icon_lbl.setText('🌿')
            self._static_title_lbl.setText('Экологический мониторинг')
            self._static_title_lbl.setStyleSheet(
                f"font-size:20px; font-weight:bold; color:{VOLGA_LIGHT};"
                f" background:transparent; border:none;"
            )
            self._static_desc_lbl.setText(
                "Готовый дашборд с KPI, временным рядом,\n"
                "категориями, географией и аналитикой\n"
                "экологической обстановки региона"
            )

            self._clear_static_tags()
            for tag_text in ["KPI", "Карта", "Временной ряд", "Анализ"]:
                tag = QLabel(tag_text)
                tag.setStyleSheet(
                    f"background:{VOLGA_DARK}; color:{VOLGA_LIGHT}; font-size:10px; font-weight:600;"
                    f" border-radius:4px; padding:3px 8px; border:none;"
                )
                self._static_tags_row.addWidget(tag)
            self._static_tags_row.setAlignment(Qt.AlignCenter)

            self._static_open_btn.setText('🚀  Открыть мониторинг')
            self._static_open_btn.setStyleSheet(
                f"QPushButton{{background:{VOLGA_DARK};color:{VOLGA_LIGHT};border:none;"
                f"border-radius:6px;font-size:14px;font-weight:bold;}}"
                f"QPushButton:hover{{background:{VOLGA_MID};color:white;}}"
            )

    def _clear_static_tags(self):
        """Удаляет все виджеты из строки тегов карточки."""
        while self._static_tags_row.count():
            item = self._static_tags_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _open_static_dashboard(self):
        """Открывает закреплённый дашборд или экомониторинг по умолчанию."""
        if self._pinned_static_path and os.path.exists(self._pinned_static_path):
            self.template_selected.emit('load_template', self._pinned_static_path)
        else:
            self.mode_selected.emit('eco')

    # ─── Данные — закреплённый дашборд ───────────────────────────────────────

    def _load_pinned_static(self) -> str | None:
        """Читает путь закреплённого дашборда из файла .pinned_static."""
        pf = os.path.join(self._templates_dir_abs(), '.pinned_static')
        if os.path.exists(pf):
            try:
                with open(pf, 'r', encoding='utf-8') as f:
                    path = f.read().strip()
                if path and os.path.exists(path):
                    return path
            except Exception:
                pass
        return None

    # ─── Действия ────────────────────────────────────────────────────────────

    def _open_configurator(self):
        self.mode_selected.emit('configurator')

    def _open_last_template(self):
        path = self._get_last_template_path()
        if path and os.path.exists(path):
            self.template_selected.emit('load_template', path)
        else:
            QMessageBox.information(
                self, "Нет сохранённых дашбордов",
                "Сначала создайте дашборд в Конструкторе и сохраните его."
            )

    def _load_selected_template(self, item: QListWidgetItem):
        if item:
            path = item.data(Qt.UserRole)
            if path and os.path.exists(path):
                self.template_selected.emit('load_template', path)

    # ─── Данные ──────────────────────────────────────────────────────────────

    def _get_last_template_path(self) -> str | None:
        last_file = os.path.join(self._templates_dir_abs(), ".last_template")
        if os.path.exists(last_file):
            try:
                with open(last_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception:
                return None
        return None

    def _save_last_template_path(self, path: str):
        tdir = self._templates_dir_abs()
        os.makedirs(tdir, exist_ok=True)
        last_file = os.path.join(tdir, ".last_template")
        with open(last_file, 'w', encoding='utf-8') as f:
            f.write(path)
        self._load_last_template_info()

    def _load_last_template_info(self):
        path = self._get_last_template_path()
        if path and os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                name = data.get('name', os.path.basename(path))
                self.last_template_name.setText(f"📊 {name}")
                self.last_template_name.setStyleSheet(
                    f"font-size:12px; color:{ACCENT}; background:transparent; border:none;"
                )
            except Exception:
                self.last_template_name.setText(os.path.basename(path))
                self.last_template_name.setStyleSheet(
                    f"font-size:12px; color:{TEXT_MUT}; background:transparent; border:none;"
                )
        else:
            self.last_template_name.setText("—")
            self.last_template_name.setStyleSheet(
                f"font-size:12px; color:{TEXT_MUT}; background:transparent; border:none;"
            )

    def _templates_dir_abs(self) -> str:
        """
        Возвращает папку для хранения дашбордов.
        Приоритет: %APPDATA%\\EcologyBI → ~/Documents/EcologyBI → project/templates/
        """
        appdata = os.environ.get('APPDATA', '')
        if appdata:
            path = os.path.join(appdata, 'EcologyBI')
            try:
                os.makedirs(path, exist_ok=True)
                return path
            except Exception:
                pass
        docs = os.path.join(os.path.expanduser('~'), 'Documents', 'EcologyBI')
        try:
            os.makedirs(docs, exist_ok=True)
            return docs
        except Exception:
            pass
        return os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
        )

    def _add_template_item(self, path: str, seen: set) -> bool:
        """Добавляет элемент в список. Возвращает True, если добавлен."""
        abs_path = os.path.abspath(path)
        if abs_path in seen or not os.path.exists(abs_path):
            return False
        seen.add(abs_path)
        file = os.path.basename(abs_path)
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            name  = data.get('name', file.replace('.json', ''))
            pages = len(data.get('pages', []))
            label = f"📊  {name}  ({pages} стр.)" if pages else f"📊  {name}"
        except Exception:
            label = f"📄  {file}"
        item = QListWidgetItem(label)
        item.setData(Qt.UserRole, abs_path)
        self.templates_list.addItem(item)
        return True

    def load_saved_templates(self):
        self.templates_list.clear()
        seen: set = set()

        tdir = self._templates_dir_abs()
        os.makedirs(tdir, exist_ok=True)

        # Дополнительные папки для обратной совместимости
        legacy_dir = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
        )
        scan_dirs = list({tdir, legacy_dir})  # дедупликация если совпадают

        # 1. Файлы напрямую в папках templates
        for d in scan_dirs:
            try:
                for file in sorted(os.listdir(d)):
                    if not file.endswith('.json') or file.startswith('.') or file.startswith('_'):
                        continue
                    self._add_template_item(os.path.join(d, file), seen)
            except Exception:
                pass

        # 2. Пути, сохранённые в манифесте (файлы из других мест)
        for d in scan_dirs:
            manifest_path = os.path.join(d, '_manifest.json')
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                    for path in manifest:
                        self._add_template_item(path, seen)
                except Exception:
                    pass

        if self.templates_list.count() == 0:
            placeholder = QListWidgetItem("Нет сохранённых дашбордов")
            placeholder.setFlags(placeholder.flags() & ~Qt.ItemIsSelectable)
            self.templates_list.addItem(placeholder)

    def update_last_template(self, path: str):
        """Вызывается из главного окна после сохранения."""
        self._save_last_template_path(path)
