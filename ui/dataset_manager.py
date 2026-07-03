# ui/dataset_manager.py
"""
Глобальный менеджер датасетов.
Синхронная загрузка — без QThread, без race conditions, без крашей.
"""

import os
import pandas as pd

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QFrame, QScrollArea,
    QLineEdit, QProgressDialog, QApplication
)

from ui.theme import (
    BG_DEEP, BG_DARK, BG_PANEL, BG_CARD, BG_HOVER,
    BORDER, BORDER_LT, BORDER_ACC,
    TEXT_PRI, TEXT_SEC, TEXT_MUT,
    ACCENT, ACCENT_DARK, ACCENT_RED, scrollbar_style
)


# ─── Строка одного датасета ───────────────────────────────────────────────────

class DatasetRow(QFrame):
    renamed = Signal(str, str)         # (old_name, new_name)
    removed = Signal(str)              # name
    edited  = Signal(str, object)      # (name, new_df)

    def __init__(self, name: str, df, parent=None):
        super().__init__(parent)
        self._name = name
        self._df   = df

        self.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 6px;
            }}
            QFrame:hover {{ border-color: {BORDER_LT}; }}
        """)
        self.setFixedHeight(60)

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 8, 8, 8)
        row.setSpacing(10)

        icon = QLabel("📊")
        icon.setStyleSheet("font-size:18px; background:transparent; border:none;")
        icon.setFixedWidth(28)
        row.addWidget(icon)

        info = QVBoxLayout()
        info.setSpacing(2)

        self._name_edit = QLineEdit(name)
        self._name_edit.setStyleSheet(
            f"QLineEdit {{ border:none; font-size:12px; font-weight:bold; color:{TEXT_PRI};"
            f" background:transparent; padding:0; }}"
            f"QLineEdit:focus {{ border-bottom:1px solid {BORDER_ACC}; }}"
        )
        self._name_edit.editingFinished.connect(self._on_rename)
        info.addWidget(self._name_edit)

        cols_preview = ", ".join(str(c) for c in list(df.columns)[:5])
        if len(df.columns) > 5:
            cols_preview += f"… (+{len(df.columns)-5})"
        meta = QLabel(f"{len(df):,} строк · {len(df.columns)} столбцов · {cols_preview}")
        meta.setStyleSheet(f"font-size:10px; color:{TEXT_MUT}; background:transparent; border:none;")
        info.addWidget(meta)

        row.addLayout(info, 1)

        edit_btn = QPushButton("✏")
        edit_btn.setFixedSize(28, 28)
        edit_btn.setToolTip("Редактировать данные")
        edit_btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;color:{TEXT_MUT};font-size:13px;}}"
            f"QPushButton:hover{{color:{ACCENT};background:{BG_HOVER};border-radius:4px;}}"
        )
        edit_btn.clicked.connect(self._on_edit)
        row.addWidget(edit_btn)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(24, 24)
        del_btn.setToolTip("Удалить датасет")
        del_btn.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;color:{BORDER_LT};font-size:14px;}}"
            f"QPushButton:hover{{color:{ACCENT_RED};background:{BG_HOVER};border-radius:4px;}}"
        )
        del_btn.clicked.connect(lambda: self.removed.emit(self._name))
        row.addWidget(del_btn)

    @property
    def name(self) -> str:
        return self._name

    def _on_rename(self):
        new = self._name_edit.text().strip()
        if new and new != self._name:
            old = self._name
            self._name = new
            self.renamed.emit(old, new)

    def _on_edit(self):
        from ui.query_editor import QueryEditorDialog
        dlg = QueryEditorDialog(self._name, self._df, parent=self.window())
        if dlg.exec() == QueryEditorDialog.Accepted:
            self._df = dlg.result_df
            self.edited.emit(self._name, self._df)


# ─── Основной диалог ─────────────────────────────────────────────────────────

class DatasetManager(QDialog):
    """
    Менеджер датасетов — загрузка CSV/Excel, именование, удаление.

    Сигналы:
        datasets_changed(dict)  — список датасетов изменился
    """

    datasets_changed = Signal(dict)

    def __init__(self, datasets: dict = None, parent=None):
        super().__init__(parent)
        self._datasets: dict = dict(datasets or {})

        self.setWindowTitle("Менеджер датасетов")
        self.setModal(True)
        self.setMinimumSize(620, 460)
        self.setStyleSheet(
            f"QDialog {{ background:{BG_DARK}; }} QLabel {{ color:{TEXT_PRI}; }}"
            f"{scrollbar_style()}"
        )

        self._build_ui()
        self._refresh()

    def get_datasets(self) -> dict:
        return dict(self._datasets)

    # ─── UI ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Заголовок
        hdr = QWidget()
        hdr.setStyleSheet(f"background:{BG_PANEL}; border-bottom:1px solid {BORDER};")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(20, 14, 20, 14)

        title_lbl = QLabel("📊  Менеджер датасетов")
        title_lbl.setStyleSheet(f"font-size:15px; font-weight:bold; color:{TEXT_PRI};")
        hdr_lay.addWidget(title_lbl)
        hdr_lay.addStretch()

        self._count_lbl = QLabel()
        self._count_lbl.setStyleSheet(f"font-size:12px; color:{TEXT_MUT};")
        hdr_lay.addWidget(self._count_lbl)

        root.addWidget(hdr)

        # Тело
        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(20, 16, 20, 16)
        body_lay.setSpacing(10)

        # Кнопка загрузки
        load_btn = QPushButton("＋  Загрузить файл (CSV / Excel)")
        load_btn.setFixedHeight(42)
        load_btn.setStyleSheet(
            f"QPushButton{{background:{ACCENT_DARK};color:{TEXT_PRI};border:none;"
            f"border-radius:8px;font-size:13px;font-weight:bold;}}"
            f"QPushButton:hover{{background:{ACCENT};color:#0F1A0F;}}"
        )
        load_btn.clicked.connect(self._load_files)
        body_lay.addWidget(load_btn)

        # Прокручиваемый список
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"QScrollArea{{background:transparent;}}{scrollbar_style()}")

        self._list_w = QWidget()
        self._list_w.setStyleSheet("background:transparent;")
        self._list_lay = QVBoxLayout(self._list_w)
        self._list_lay.setContentsMargins(0, 0, 4, 0)
        self._list_lay.setSpacing(8)
        self._list_lay.addStretch()

        scroll.setWidget(self._list_w)
        body_lay.addWidget(scroll, 1)

        # Пустое состояние
        self._empty_lbl = QLabel(
            "Нет загруженных датасетов.\n"
            "Нажмите «Загрузить файл», чтобы добавить CSV или Excel."
        )
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._empty_lbl.setStyleSheet(f"color:{TEXT_MUT};font-size:13px;padding:40px;")
        body_lay.addWidget(self._empty_lbl)

        root.addWidget(body, 1)

        # Футер
        ftr = QWidget()
        ftr.setStyleSheet(f"background:{BG_PANEL};border-top:1px solid {BORDER};")
        ftr_lay = QHBoxLayout(ftr)
        ftr_lay.setContentsMargins(20, 10, 20, 10)

        hint = QLabel("Выберите датасет в настройках каждого виджета.")
        hint.setStyleSheet(f"font-size:11px;color:{TEXT_MUT};")
        ftr_lay.addWidget(hint)
        ftr_lay.addStretch()

        close_btn = QPushButton("Закрыть")
        close_btn.setFixedHeight(34)
        close_btn.setStyleSheet(
            f"QPushButton{{background:{BG_CARD};border:1px solid {BORDER};"
            f"border-radius:6px;padding:0 20px;font-size:12px;color:{TEXT_SEC};}}"
            f"QPushButton:hover{{background:{BG_HOVER};border-color:{BORDER_LT};}}"
        )
        close_btn.clicked.connect(self.accept)
        ftr_lay.addWidget(close_btn)

        root.addWidget(ftr)

    # ─── Список ───────────────────────────────────────────────────────────────

    def _refresh(self):
        # Убираем все строки (кроме stretch)
        while self._list_lay.count() > 1:
            item = self._list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for name, df in self._datasets.items():
            row = DatasetRow(name, df)
            row.renamed.connect(self._on_renamed)
            row.removed.connect(self._on_removed)
            row.edited.connect(self._on_edited)
            self._list_lay.insertWidget(self._list_lay.count() - 1, row)

        has = bool(self._datasets)
        self._empty_lbl.setVisible(not has)
        n = len(self._datasets)
        self._count_lbl.setText(
            f"{n} датасет{'а' if 2 <= n <= 4 else 'ов' if n != 1 else ''}" if n else ""
        )

    def _on_renamed(self, old: str, new: str):
        if new in self._datasets and new != old:
            QMessageBox.warning(self, "Имя занято", f"Датасет «{new}» уже существует.")
            return
        df = self._datasets.pop(old)
        # Пересобираем dict с сохранением порядка
        self._datasets = {(new if k == old else k): v for k, v in {**self._datasets, new: df}.items()}
        self.datasets_changed.emit(self._datasets)

    def _on_removed(self, name: str):
        self._datasets.pop(name, None)
        self._refresh()
        self.datasets_changed.emit(self._datasets)

    def _on_edited(self, name: str, new_df):
        self._datasets[name] = new_df
        self._refresh()
        self.datasets_changed.emit(self._datasets)

    # ─── Загрузка (синхронная) ────────────────────────────────────────────────

    def _load_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Загрузить датасеты", "",
            "CSV и Excel (*.csv *.xlsx *.xls);;CSV (*.csv);;Excel (*.xlsx *.xls)"
        )
        if not paths:
            return

        progress = QProgressDialog("Загрузка файлов…", "Отмена", 0, len(paths), self)
        progress.setWindowTitle("Загрузка")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        errors = []
        for i, path in enumerate(paths):
            if progress.wasCanceled():
                break

            fname = os.path.basename(path)
            progress.setLabelText(f"Загружаю: {fname}")
            progress.setValue(i)
            QApplication.processEvents()

            try:
                ext = os.path.splitext(path)[1].lower()
                if ext == '.csv':
                    # Пробуем несколько кодировок
                    df = None
                    for enc in ('utf-8-sig', 'cp1251', 'latin-1'):
                        try:
                            df = pd.read_csv(path, encoding=enc)
                            break
                        except UnicodeDecodeError:
                            continue
                    if df is None:
                        raise ValueError("Не удалось определить кодировку файла")
                elif ext in ('.xlsx', '.xls'):
                    df = pd.read_excel(path)
                else:
                    errors.append(f"{fname}: неподдерживаемый формат")
                    continue

                # Уникальное имя
                name = os.path.splitext(fname)[0]
                base, j = name, 2
                while name in self._datasets:
                    name = f"{base} ({j})"
                    j += 1
                self._datasets[name] = df

            except Exception as e:
                errors.append(f"{fname}: {e}")

        progress.setValue(len(paths))
        progress.close()

        if errors:
            QMessageBox.warning(
                self, "Ошибки загрузки",
                "Не удалось загрузить:\n\n" + "\n".join(errors)
            )

        self._refresh()
        if self._datasets:
            self.datasets_changed.emit(self._datasets)
