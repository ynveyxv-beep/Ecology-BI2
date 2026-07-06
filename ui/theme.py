# ui/theme.py
"""
Тема Ecology-BI — «Slate Dark» (Vercel / Linear style).
Импортируй константы отсюда, не дублируй по файлам.
"""

# ─── Фон ──────────────────────────────────────────────────────────────────────
BG_DEEP     = "#060B18"   # глубочайший фон — корень приложения
BG_DARK     = "#0F172A"   # основной фон (slate-900)
BG_PANEL    = "#1E293B"   # панели, тулбар (slate-800)
BG_CARD     = "#263347"   # карточки, ячейки (slate-750)
BG_HOVER    = "#2D3E56"   # hover-состояние
BG_ACTIVE   = "#1D3A5C"   # активный / выбранный элемент

# ─── Границы ──────────────────────────────────────────────────────────────────
BORDER      = "#334155"   # спокойная граница (slate-700)
BORDER_LT   = "#475569"   # немного ярче (slate-600)
BORDER_ACC  = "#38BDF8"   # акцентная граница — cyan-400

# ─── Текст ────────────────────────────────────────────────────────────────────
TEXT_PRI    = "#F1F5F9"   # основной текст (slate-100)
TEXT_SEC    = "#94A3B8"   # вторичный (slate-400)
TEXT_MUT    = "#64748B"   # приглушённый (slate-500)

# ─── Акценты ──────────────────────────────────────────────────────────────────
ACCENT      = "#38BDF8"   # cyan-400 — основной акцент
ACCENT_DARK = "#0284C7"   # cyan-600 — кнопки, бэкграунд акцента
ACCENT_GLOW = "#7DD3FC"   # cyan-300 — hover-подсветка
ACCENT_RED  = "#F87171"   # red-400 — предупреждение / удаление
ACCENT_GOLD = "#FBBF24"   # amber-400 — второстепенный акцент

# ─── Волга (бирюзово-синие тона для карты) ────────────────────────────────────
VOLGA_DARK  = "#164E63"   # cyan-950
VOLGA_MID   = "#0E7490"   # cyan-700
VOLGA_LIGHT = "#22D3EE"   # cyan-400

# ─── Скругления ───────────────────────────────────────────────────────────────
RADIUS      = "6px"       # стандартное скругление
RADIUS_SM   = "4px"       # маленькое — кнопки, теги
RADIUS_LG   = "10px"      # большое — карточки, диалоги

# ─── Палитра графиков ─────────────────────────────────────────────────────────
CHART_PALETTE = [
    "#38BDF8",   # cyan    — основной
    "#818CF8",   # indigo  — второй
    "#FBBF24",   # amber   — третий
    "#F87171",   # red     — четвёртый
    "#34D399",   # emerald — пятый
    "#A78BFA",   # violet  — шестой
    "#F472B6",   # pink    — седьмой
    "#4ADE80",   # green   — восьмой
]

# ─── Список доступных тем ─────────────────────────────────────────────────────
THEME_LIST = [
    ('slate_dark',  'Тёмный Slate'),
    ('forest_dark', 'Тёмный Лес'),
    ('ocean_dark',  'Тёмный Океан'),
    ('light',       'Светлый'),
]

CURRENT_THEME_NAME = 'slate_dark'

# ─── Реестр коллбэков при смене темы ─────────────────────────────────────────
_theme_callbacks: list = []


def register_theme_callback(fn) -> None:
    """Регистрирует функцию, которая вызывается при смене темы."""
    if fn not in _theme_callbacks:
        _theme_callbacks.append(fn)


def unregister_theme_callback(fn) -> None:
    """Удаляет ранее зарегистрированный коллбэк."""
    try:
        _theme_callbacks.remove(fn)
    except ValueError:
        pass


# ─── Хранилище тем ────────────────────────────────────────────────────────────
_THEMES = {
    'slate_dark': {
        'BG_DEEP':    "#060B18",
        'BG_DARK':    "#0F172A",
        'BG_PANEL':   "#1E293B",
        'BG_CARD':    "#263347",
        'BG_HOVER':   "#2D3E56",
        'BG_ACTIVE':  "#1D3A5C",
        'BORDER':     "#334155",
        'BORDER_LT':  "#475569",
        'BORDER_ACC': "#38BDF8",
        'TEXT_PRI':   "#F1F5F9",
        'TEXT_SEC':   "#94A3B8",
        'TEXT_MUT':   "#64748B",
        'ACCENT':     "#38BDF8",
        'ACCENT_DARK':"#0284C7",
        'ACCENT_GLOW':"#7DD3FC",
        'ACCENT_RED': "#F87171",
    },
    'forest_dark': {
        'BG_DEEP':    "#030A03",
        'BG_DARK':    "#0A1A0A",
        'BG_PANEL':   "#152515",
        'BG_CARD':    "#1C331C",
        'BG_HOVER':   "#244024",
        'BG_ACTIVE':  "#1A4A1A",
        'BORDER':     "#2A4A2A",
        'BORDER_LT':  "#3A6A3A",
        'BORDER_ACC': "#4ADE80",
        'TEXT_PRI':   "#F0FFF0",
        'TEXT_SEC':   "#86A886",
        'TEXT_MUT':   "#507050",
        'ACCENT':     "#4ADE80",
        'ACCENT_DARK':"#16A34A",
        'ACCENT_GLOW':"#86EFAC",
        'ACCENT_RED': "#F87171",
    },
    'ocean_dark': {
        'BG_DEEP':    "#020810",
        'BG_DARK':    "#0A1020",
        'BG_PANEL':   "#101828",
        'BG_CARD':    "#182035",
        'BG_HOVER':   "#202845",
        'BG_ACTIVE':  "#162040",
        'BORDER':     "#243050",
        'BORDER_LT':  "#344060",
        'BORDER_ACC': "#60A0F0",
        'TEXT_PRI':   "#F0F4FF",
        'TEXT_SEC':   "#8090B8",
        'TEXT_MUT':   "#506080",
        'ACCENT':     "#60A0F0",
        'ACCENT_DARK':"#2060C0",
        'ACCENT_GLOW':"#90C0FF",
        'ACCENT_RED': "#F87171",
    },
    'light': {
        'BG_DEEP':    "#E8ECF0",
        'BG_DARK':    "#F1F5F9",
        'BG_PANEL':   "#FFFFFF",
        'BG_CARD':    "#F8FAFC",
        'BG_HOVER':   "#EEF2F7",
        'BG_ACTIVE':  "#DBEAFE",
        'BORDER':     "#CBD5E1",
        'BORDER_LT':  "#94A3B8",
        'BORDER_ACC': "#2563EB",
        'TEXT_PRI':   "#0F172A",
        'TEXT_SEC':   "#475569",
        'TEXT_MUT':   "#94A3B8",
        'ACCENT':     "#2563EB",
        'ACCENT_DARK':"#1D4ED8",
        'ACCENT_GLOW':"#3B82F6",
        'ACCENT_RED': "#DC2626",
    },
}

# 'ocean' — устаревший алиас для старых сохранённых проектов
_THEMES['ocean'] = _THEMES['ocean_dark']

# Публичный алиас — используется в html_exporter и других модулях
THEMES = _THEMES


def set_active_theme(name: str):
    """
    Применяет тему по имени — обновляет все модульные переменные в этом модуле.
    Вызывай после смены темы, затем обновляй inline-стили виджетов.
    """
    global CURRENT_THEME_NAME
    global BG_DEEP, BG_DARK, BG_PANEL, BG_CARD, BG_HOVER, BG_ACTIVE
    global BORDER, BORDER_LT, BORDER_ACC
    global TEXT_PRI, TEXT_SEC, TEXT_MUT
    global ACCENT, ACCENT_DARK, ACCENT_GLOW, ACCENT_RED

    theme = _THEMES.get(name, _THEMES['slate_dark'])
    CURRENT_THEME_NAME = name

    BG_DEEP    = theme['BG_DEEP']
    BG_DARK    = theme['BG_DARK']
    BG_PANEL   = theme['BG_PANEL']
    BG_CARD    = theme['BG_CARD']
    BG_HOVER   = theme['BG_HOVER']
    BG_ACTIVE  = theme['BG_ACTIVE']
    BORDER     = theme['BORDER']
    BORDER_LT  = theme['BORDER_LT']
    BORDER_ACC = theme['BORDER_ACC']
    TEXT_PRI   = theme['TEXT_PRI']
    TEXT_SEC   = theme['TEXT_SEC']
    TEXT_MUT   = theme['TEXT_MUT']
    ACCENT     = theme['ACCENT']
    ACCENT_DARK = theme['ACCENT_DARK']
    ACCENT_GLOW = theme['ACCENT_GLOW']
    ACCENT_RED  = theme['ACCENT_RED']

    # Уведомить всех подписчиков о смене темы
    for _fn in list(_theme_callbacks):
        try:
            _fn()
        except Exception:
            pass


def get_palette() -> dict:
    """Returns current theme colors as a dict. Useful for widgets that need
    to pick up theme changes at runtime."""
    return {
        'BG_DEEP':    BG_DEEP,
        'BG_DARK':    BG_DARK,
        'BG_PANEL':   BG_PANEL,
        'BG_CARD':    BG_CARD,
        'BG_HOVER':   BG_HOVER,
        'BG_ACTIVE':  BG_ACTIVE,
        'BORDER':     BORDER,
        'BORDER_LT':  BORDER_LT,
        'BORDER_ACC': BORDER_ACC,
        'TEXT_PRI':   TEXT_PRI,
        'TEXT_SEC':   TEXT_SEC,
        'TEXT_MUT':   TEXT_MUT,
        'ACCENT':     ACCENT,
        'ACCENT_DARK':ACCENT_DARK,
        'ACCENT_GLOW':ACCENT_GLOW,
        'ACCENT_RED': ACCENT_RED,
    }


# ─── Готовые stylesheet-блоки ─────────────────────────────────────────────────

def scrollbar_style(track=None, handle=None, hover=None):
    t = track  if track  is not None else BG_DARK
    h = handle if handle is not None else BORDER
    hv= hover  if hover  is not None else BORDER_LT
    return f"""
        QScrollBar:vertical {{
            background: {t}; width: 6px; margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {h}; border-radius: 3px; min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {hv}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{
            background: {t}; height: 6px; margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background: {h}; border-radius: 3px; min-width: 24px;
        }}
        QScrollBar::handle:horizontal:hover {{ background: {hv}; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    """


def app_stylesheet():
    """Глобальный стиль всего приложения."""
    return f"""
        QWidget {{
            background: {BG_DARK};
            color: {TEXT_PRI};
            font-family: 'Segoe UI', 'Inter', 'SF Pro Display', sans-serif;
            font-size: 13px;
        }}
        QMainWindow {{ background: {BG_DEEP}; }}
        QDialog {{ background: {BG_DARK}; }}
        QLabel {{ color: {TEXT_PRI}; background: transparent; }}
        QToolTip {{
            background: {BG_PANEL}; color: {TEXT_PRI};
            border: 1px solid {BORDER_LT}; border-radius: {RADIUS_SM}; padding: 4px 8px;
            font-size: 12px;
        }}
        /* BUG 4 FIX: explicit color on QPushButton so text never blends into background */
        QPushButton {{
            background: {BG_CARD};
            color: {TEXT_PRI};
            border: 1px solid {BORDER};
            border-radius: {RADIUS};
            padding: 5px 12px;
            font-size: 12px;
        }}
        QPushButton:hover  {{ background: {BG_HOVER}; border-color: {BORDER_LT}; color: {TEXT_PRI}; }}
        QPushButton:pressed {{ background: {BG_ACTIVE}; }}
        QPushButton:disabled {{ color: {TEXT_MUT}; background: {BG_PANEL}; border-color: {BORDER}; }}
        /* BUG 8 FIX: ensure QMessageBox text is always readable */
        QMessageBox {{
            background: {BG_DARK};
            color: {TEXT_PRI};
        }}
        QMessageBox QLabel {{
            color: {TEXT_PRI};
            background: transparent;
            font-size: 13px;
        }}
        QMessageBox QPushButton {{
            background: {BG_CARD};
            color: {TEXT_PRI};
            border: 1px solid {BORDER};
            border-radius: {RADIUS};
            padding: 5px 16px;
            min-width: 60px;
        }}
        QMessageBox QPushButton:hover {{ background: {BG_HOVER}; border-color: {BORDER_LT}; }}
        QComboBox {{
            background: {BG_CARD}; color: {TEXT_PRI};
            border: 1px solid {BORDER}; border-radius: {RADIUS};
            padding: 5px 10px; font-size: 12px; min-height: 30px;
        }}
        QComboBox:hover  {{ border-color: {BORDER_LT}; }}
        QComboBox:focus  {{ border-color: {BORDER_ACC}; }}
        QComboBox::drop-down {{ border: none; width: 22px; }}
        QComboBox QAbstractItemView {{
            background: {BG_PANEL}; color: {TEXT_PRI};
            border: 1px solid {BORDER_LT}; border-radius: {RADIUS};
            selection-background-color: {BG_ACTIVE};
            selection-color: {ACCENT}; outline: 0; padding: 4px;
        }}
        QComboBox QAbstractItemView::item {{
            min-height: 28px; padding: 0 8px; border-radius: {RADIUS_SM};
        }}
        QComboBox QAbstractItemView::item:hover {{ background: {BG_HOVER}; }}
        QLineEdit {{
            background: {BG_CARD}; color: {TEXT_PRI};
            border: 1px solid {BORDER}; border-radius: {RADIUS};
            padding: 5px 10px; font-size: 12px; min-height: 30px;
        }}
        QLineEdit:hover {{ border-color: {BORDER_LT}; }}
        QLineEdit:focus {{ border-color: {BORDER_ACC}; }}
        QSpinBox {{
            background: {BG_CARD}; color: {TEXT_PRI};
            border: 1px solid {BORDER}; border-radius: {RADIUS};
            padding: 4px 8px; font-size: 12px; min-height: 30px;
        }}
        QSpinBox:focus {{ border-color: {BORDER_ACC}; }}
        QCheckBox {{ color: {TEXT_PRI}; font-size: 12px; spacing: 6px; }}
        QCheckBox::indicator {{
            width: 16px; height: 16px;
            border: 1px solid {BORDER_LT}; border-radius: {RADIUS_SM};
            background: {BG_CARD};
        }}
        QCheckBox::indicator:checked {{
            background: {ACCENT_DARK}; border-color: {ACCENT};
        }}
        QTextEdit {{
            background: {BG_CARD}; color: {TEXT_PRI};
            border: 1px solid {BORDER}; border-radius: {RADIUS}; padding: 6px 10px;
        }}
        QScrollArea {{ background: transparent; border: none; }}
        {scrollbar_style()}
    """
