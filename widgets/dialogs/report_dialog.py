# widgets/dialogs/report_dialog.py
"""
Диалог параметров отчёта перед генерацией.
Поля: организация, период, составитель, примечание.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QFrame, QWidget
)

from ui.theme import (
    BG_DARK, BG_PANEL, BG_CARD, BG_HOVER, BORDER, BORDER_LT,
    ACCENT, ACCENT_DARK, TEXT_PRI, TEXT_SEC, TEXT_MUT,
    RADIUS_SM,
)

_STYLE = f"""
QDialog {{ background:{BG_DARK}; color:{TEXT_PRI}; }}
QLabel  {{ color:{TEXT_SEC}; font-size:11px; background:transparent; border:none; }}
QLineEdit, QTextEdit {{
  background:{BG_CARD}; border:1px solid {BORDER};
  border-radius:{RADIUS_SM}; color:{TEXT_PRI};
  padding:5px 8px; font-size:12px;
  selection-background-color:{ACCENT_DARK};
}}
QLineEdit:focus, QTextEdit:focus {{ border-color:{ACCENT}; }}
"""

_BTN_OK = f"""
QPushButton {{
  background:{ACCENT_DARK}; color:#0F172A;
  border:none; border-radius:{RADIUS_SM};
  padding:8px 24px; font-weight:600; font-size:13px;
}}
QPushButton:hover {{ background:{ACCENT}; }}
"""

_BTN_CANCEL = f"""
QPushButton {{
  background:{BG_CARD}; color:{TEXT_SEC};
  border:1px solid {BORDER}; border-radius:{RADIUS_SM};
  padding:8px 18px; font-size:12px;
}}
QPushButton:hover {{ background:{BG_HOVER}; border-color:{BORDER_LT}; color:{TEXT_PRI}; }}
"""


class ReportDialog(QDialog):
    """Диалог ввода параметров отчёта."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Формирование отчёта")
        self.setMinimumWidth(420)
        self.setModal(True)
        self.setStyleSheet(_STYLE)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # Заголовок
        title = QLabel("Параметры отчёта")
        title.setStyleSheet(f"font-size:16px; font-weight:700; color:{TEXT_PRI};")
        root.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background:{BORDER}; max-height:1px;")
        root.addWidget(sep)

        # Форма
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.org_edit = QLineEdit()
        self.org_edit.setPlaceholderText("МКУ «Экология Нижнего Новгорода»")
        form.addRow("Организация:", self.org_edit)

        self.period_edit = QLineEdit()
        self.period_edit.setPlaceholderText("Июнь 2026")
        form.addRow("Период:", self.period_edit)

        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("Иванов И. И., эколог")
        form.addRow("Составил:", self.author_edit)

        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Краткое описание / подзаголовок (необязательно)...")
        self.note_edit.setMaximumHeight(70)
        form.addRow("Примечание:", self.note_edit)

        root.addLayout(form)

        # Hint
        hint = QLabel("После нажатия «Сформировать» выберите путь сохранения.\nОтчёт откроется в браузере. Для PDF — нажмите «Печать / PDF» на странице.")
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"font-size:11px; color:{TEXT_MUT}; background:{BG_PANEL};"
            f"border:1px solid {BORDER}; border-radius:6px; padding:8px 12px;"
        )
        root.addWidget(hint)

        # Кнопки
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel = QPushButton("Отмена")
        cancel.setStyleSheet(_BTN_CANCEL)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)

        ok = QPushButton("Сформировать →")
        ok.setStyleSheet(_BTN_OK)
        ok.setDefault(True)
        ok.clicked.connect(self.accept)
        btn_row.addWidget(ok)

        root.addLayout(btn_row)

    # ── Данные ──────────────────────────────────────────────────────────────

    def get_params(self) -> dict:
        return {
            'org_name': self.org_edit.text().strip(),
            'period':   self.period_edit.text().strip(),
            'author':   self.author_edit.text().strip(),
            'note':     self.note_edit.toPlainText().strip(),
        }
