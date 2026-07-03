# ui/data_panel.py
"""
Панель управления данными дашборда.

Позволяет:
- Загрузить несколько файлов (CSV / Excel) одновременно
- Видеть прогресс загрузки каждого файла
- Удалять файлы из списка
- Применить данные к дашборду (объединение или выбор)
"""

from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QProgressBar, QScrollArea, QFrame,
    QSizePolicy, QMessageBox, QComboBox
)
from PySide6.QtGui import QColor

import os
import traceback


# ─── Поток загрузки файла ──────────────────────────────────────────────────────

class DataLoaderThread(QThread):
    """
    Загружает один файл в отдельном потоке.
    Сигналы: progress(0-100), loaded(path, df), error(path, message)
    """
    progress = Signal(int)          # 0–100
    loaded   = Signal(str, object)  # (path, DataFrame)
    error    = Signal(str, str)     # (path, error_message)

    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self._path = path

    def run(self):
        try:
            self.progress.emit(10)
            from core.data_manager import DataManager
            dm = DataManager()
            self.progress.emit(40)
            df = dm.load_file(self._path)
            self.progress.emit(90)
            self.loaded.emit(self._path, df)
            self.progress.emit(100)
        except Exception as e:
            self.error.emit(self._path, str(e))


# ─── Строка файла в списке ────────────────────────────────────────────────────

class FileRow(QFrame):
    """Строка в списке загруженных файлов."""
    remove_requested = Signal(str)   # path

    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self.path = path
        self._df  = None
        self.setFixedHeight(56)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E8EAF0;
                border-radius: 8px;
            }
        """)

        h = QHBoxLayout(self)
        h.setContentsMargins(12, 6, 8, 6)
        h.setSpacing(10)

        # Иконка
        self._icon = QLabel("⏳")
        self._icon.setFixedWidth(20)
        self._icon.setAlignment(Qt.AlignCenter)
        self._icon.setStyleSheet("border:none; font-size:16px;")
        h.addWidget(self._icon)

        # Текст (имя файла + статус)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self._name_lbl = QLabel(os.path.basename(path))
        self._name_lbl.setStyleSheet(
            "font-size:12px; font-weight:600; color:#1A1D27; border:none;"
        )
        text_col.addWidget(self._name_lbl)

        self._status_lbl = QLabel("Загружается…")
        self._status_lbl.setStyleSheet(
            "font-size:10px; color:#9099AD; border:none;"
        )
        text_col.addWidget(self._status_lbl)
        h.addLayout(text_col, 1)

        # Прогресс-бар
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setFixedWidth(90)
        self._bar.setFixedHeight(6)
        self._bar.setTextVisible(False)
        self._bar.setStyleSheet("""
            QProgressBar {
                background: #F0F0F6;
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background: #5282FF;
                border-radius: 3px;
            }
        """)
        h.addWidget(self._bar)

        # Кнопка удалить
        rm_btn = QPushButton("✕")
        rm_btn.setFixedSize(24, 24)
        rm_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                font-size: 13px; color: #C8CADE;
            }
            QPushButton:hover { color: #FF5252; }
        """)
        rm_btn.clicked.connect(lambda: self.remove_requested.emit(self.path))
        h.addWidget(rm_btn)

    def set_progress(self, value: int):
        self._bar.setValue(value)

    def set_loaded(self, df):
        self._df = df
        self._icon.setText("✅")
        self._bar.setValue(100)
        self._bar.setStyleSheet("""
            QProgressBar { background:#F0F0F6; border-radius:3px; border:none; }
            QProgressBar::chunk { background:#28a745; border-radius:3px; }
        """)
        self._status_lbl.setText(f"{len(df):,} строк · {len(df.columns)} столбцов")
        self._status_lbl.setStyleSheet("font-size:10px; color:#28a745; border:none;")

    def set_error(self, message: str):
        self._icon.setText("❌")
        self._bar.setValue(0)
        self._status_lbl.setText(f"Ошибка: {message[:60]}")
        self._status_lbl.setStyleSheet("font-size:10px; color:#dc3545; border:none;")

    @property
    def df(self):
        return self._df


# ─── Основная панель данных ───────────────────────────────────────────────────

class DataPanel(QDialog):
    """
    Диалог управления наборами данных дашборда.

    Сигнал data_ready(df) — передаёт итоговый DataFrame в configurator.
    """
    data_ready = Signal(object)   # pandas DataFrame

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Данные дашборда")
        self.setModal(True)
        self.setMinimumSize(520, 400)
        self.setMaximumWidth(620)

        self._file_rows   = {}    # path → FileRow
        self._threads     = {}    # path → DataLoaderThread
        self._loaded_dfs  = {}    # path → DataFrame

        self.setStyleSheet("""
            QDialog { background: #F8F9FB; }
            QLabel  { color: #333; }
            QPushButton {
                background: #F3F5F7; border: 1px solid #E0E2E6;
                border-radius: 6px; padding: 6px 16px;
                font-size: 12px; color: #333;
            }
            QPushButton:hover { background: #E8EAED; border-color: #C8CAD0; }
            QComboBox {
                background: white; border: 1px solid #D0D3DA;
                border-radius: 6px; padding: 5px 10px;
                font-size: 12px; color: #1A1D27; min-height: 28px;
            }
            QComboBox QAbstractItemView {
                background: white; color: #1A1D27;
                selection-background-color: #EEF2FF;
                selection-color: #5282FF;
            }
        """)

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # Заголовок
        title = QLabel("Источники данных")
        title.setStyleSheet("font-size:15px; font-weight:bold; color:#1A1D27;")
        root.addWidget(title)

        subtitle = QLabel(
            "Загрузите один или несколько CSV / Excel файлов. "
            "Если файлов несколько — данные будут объединены."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size:11px; color:#9099AD;")
        root.addWidget(subtitle)

        # Кнопка «Добавить файлы»
        add_btn = QPushButton("＋  Добавить файлы…")
        add_btn.setStyleSheet("""
            QPushButton {
                background: #5282FF; color: white;
                border: none; border-radius: 6px;
                padding: 8px 20px; font-size: 12px; font-weight: 600;
            }
            QPushButton:hover { background: #3d6eee; }
        """)
        add_btn.clicked.connect(self._pick_files)
        root.addWidget(add_btn, alignment=Qt.AlignLeft)

        # Список файлов
        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(6)
        self._list_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setMinimumHeight(160)
        scroll.setWidget(self._list_container)
        root.addWidget(scroll, 1)

        # Пустой placeholder
        self._empty_lbl = QLabel("Файлы не загружены.\nНажмите «Добавить файлы», чтобы начать.")
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._empty_lbl.setStyleSheet(
            "font-size:12px; color:#B0B5C8; padding:30px;"
        )
        self._list_layout.insertWidget(0, self._empty_lbl)

        # Режим объединения (показывается когда файлов > 1)
        self._merge_row = QWidget()
        merge_h = QHBoxLayout(self._merge_row)
        merge_h.setContentsMargins(0, 0, 0, 0)
        merge_h.setSpacing(8)
        merge_h.addWidget(QLabel("Если несколько файлов:"))
        self._merge_combo = QComboBox()
        self._merge_combo.addItem("Объединить все (склеить строки)", "concat")
        self._merge_combo.addItem("Использовать только первый файл", "first")
        self._merge_combo.addItem("Использовать только последний файл", "last")
        merge_h.addWidget(self._merge_combo, 1)
        self._merge_row.hide()
        root.addWidget(self._merge_row)

        # Итоговый прогресс
        self._total_bar = QProgressBar()
        self._total_bar.setRange(0, 100)
        self._total_bar.setValue(0)
        self._total_bar.setTextVisible(False)
        self._total_bar.setFixedHeight(6)
        self._total_bar.setStyleSheet("""
            QProgressBar { background:#F0F0F6; border-radius:3px; border:none; }
            QProgressBar::chunk { background:#5282FF; border-radius:3px; }
        """)
        self._total_bar.hide()
        root.addWidget(self._total_bar)

        self._total_status = QLabel("")
        self._total_status.setStyleSheet("font-size:11px; color:#9099AD;")
        self._total_status.hide()
        root.addWidget(self._total_status)

        # Нижние кнопки
        btns = QHBoxLayout()
        btns.setSpacing(8)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)

        btns.addStretch()

        self._apply_btn = QPushButton("✓  Применить к дашборду")
        self._apply_btn.setEnabled(False)
        self._apply_btn.setFixedHeight(38)
        self._apply_btn.setStyleSheet("""
            QPushButton {
                background: #28a745; color: white;
                border: none; border-radius: 6px;
                padding: 6px 20px; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover   { background: #218838; }
            QPushButton:disabled { background: #C8D4CA; color: #aaa; }
        """)
        self._apply_btn.clicked.connect(self._apply)
        btns.addWidget(self._apply_btn)

        root.addLayout(btns)

    # ─── Выбор файлов ──────────────────────────────────────────────────────

    def _pick_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите файлы с данными",
            "",
            "Данные (*.csv *.xlsx *.xls);;CSV (*.csv);;Excel (*.xlsx *.xls)"
        )
        for path in paths:
            if path and path not in self._file_rows:
                self._add_file(path)

    def _add_file(self, path: str):
        # Убираем placeholder
        self._empty_lbl.hide()

        row = FileRow(path)
        row.remove_requested.connect(self._remove_file)
        self._file_rows[path] = row
        # Вставляем перед stretch
        idx = self._list_layout.count() - 1
        self._list_layout.insertWidget(idx, row)

        self._update_merge_visibility()
        self._update_progress_bar()

        # Запускаем загрузку в отдельном потоке
        thread = DataLoaderThread(path)
        thread.progress.connect(lambda v, p=path: self._on_progress(p, v))
        thread.loaded.connect(self._on_loaded)
        thread.error.connect(self._on_error)
        self._threads[path] = thread
        thread.start()

    def _remove_file(self, path: str):
        row = self._file_rows.pop(path, None)
        if row:
            self._list_layout.removeWidget(row)
            row.deleteLater()

        self._loaded_dfs.pop(path, None)

        thread = self._threads.pop(path, None)
        if thread and thread.isRunning():
            thread.quit()
            thread.wait(300)

        if not self._file_rows:
            self._empty_lbl.show()

        self._update_merge_visibility()
        self._update_apply_button()
        self._update_progress_bar()

    # ─── Callbacks потока ──────────────────────────────────────────────────

    def _on_progress(self, path: str, value: int):
        row = self._file_rows.get(path)
        if row:
            row.set_progress(value)
        self._update_progress_bar()

    def _on_loaded(self, path: str, df):
        self._loaded_dfs[path] = df
        row = self._file_rows.get(path)
        if row:
            row.set_loaded(df)
        self._update_progress_bar()
        self._update_apply_button()

    def _on_error(self, path: str, message: str):
        row = self._file_rows.get(path)
        if row:
            row.set_error(message)
        self._update_progress_bar()

    # ─── UI helpers ────────────────────────────────────────────────────────

    def _update_merge_visibility(self):
        self._merge_row.setVisible(len(self._file_rows) > 1)

    def _update_apply_button(self):
        self._apply_btn.setEnabled(bool(self._loaded_dfs))

    def _update_progress_bar(self):
        total = len(self._file_rows)
        if total == 0:
            self._total_bar.hide()
            self._total_status.hide()
            return

        done  = len(self._loaded_dfs)
        pct   = int(done / total * 100) if total else 0
        self._total_bar.show()
        self._total_bar.setValue(pct)

        if done < total:
            self._total_status.setText(f"Загружено {done} из {total} файлов…")
            self._total_status.show()
        else:
            total_rows = sum(len(df) for df in self._loaded_dfs.values())
            self._total_status.setText(f"✅ Все файлы загружены · итого {total_rows:,} строк")
            self._total_status.show()

    # ─── Применение данных ─────────────────────────────────────────────────

    def _apply(self):
        if not self._loaded_dfs:
            return

        try:
            import pandas as pd
            dfs = list(self._loaded_dfs.values())

            mode = self._merge_combo.currentData() if len(dfs) > 1 else "first"

            if mode == "concat" and len(dfs) > 1:
                df = pd.concat(dfs, ignore_index=True)
            elif mode == "last":
                df = dfs[-1]
            else:
                df = dfs[0]

            self.data_ready.emit(df)
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось объединить данные:\n{e}")
