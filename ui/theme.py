# ui/theme.py
"""
Тема Ecology-BI — поддержка 6 встроенных тем.
Импортируй константы отсюда, не дублируй по файлам.
"""

# ─── Таблица тем ──────────────────────────────────────────────────────────────

THEMES = {
    'ocean': {
        'name':         '🌊 Ocean',
        'BG_DEEP':      '#060B18',
        'BG_DARK':      '#0F172A',
        'BG_PANEL':     '#1E293B',
        'BG_CARD':      '#263347',
        'BG_HOVER':     '#2D3E56',
        'BG_ACTIVE':    '#1D3A5C',
        'BORDER':       '#334155',
        'BORDER_LT':    '#475569',
        'BORDER_ACC':   '#38BDF8',
        'TEXT_PRI':     '#F1F5F9',
        'TEXT_SEC':     '#94A3B8',
        'TEXT_MUT':     '#64748B',
        'ACCENT':       '#38BDF8',
        'ACCENT_DARK':  '#0284C7',
        'ACCENT_GLOW':  '#7DD3FC',
        'ACCENT_RED':   '#F87171',
        'ACCENT_GOLD':  '#FBBF24',
        'CHART_PALETTE': ['#38BDF8','#818CF8','#FBBF24','#F87171',
                          '#34D399','#A78BFA','#F472B6','#4ADE80'],
    },
    'emerald': {
        'name':         '🌿 Emerald',
        'BG_DEEP':      '#030d07',
        'BG_DARK':      '#081a0f',
        'BG_PANEL':     '#0e2718',
        'BG_CARD':      '#153320',
        'BG_HOVER':     '#1c4229',
        'BG_ACTIVE':    '#1a3d26',
        'BORDER':       '#1e5733',
        'BORDER_LT':    '#2d7a47',
        'BORDER_ACC':   '#4ade80',
        'TEXT_PRI':     '#f0fdf4',
        'TEXT_SEC':     '#86efac',
        'TEXT_MUT':     '#4d9966',
        'ACCENT':       '#4ade80',
        'ACCENT_DARK':  '#16a34a',
        'ACCENT_GLOW':  '#bbf7d0',
        'ACCENT_RED':   '#f87171',
        'ACCENT_GOLD':  '#fbbf24',
        'CHART_PALETTE': ['#4ade80','#34d399','#86efac','#fbbf24',
                          '#38bdf8','#a78bfa','#f472b6','#f87171'],
    },
    'midnight': {
        'name':         '🌌 Midnight',
        'BG_DEEP':      '#05030f',
        'BG_DARK':      '#0c0a1e',
        'BG_PANEL':     '#1a1730',
        'BG_CARD':      '#231f3e',
        'BG_HOVER':     '#2d2855',
        'BG_ACTIVE':    '#2a2460',
        'BORDER':       '#3b3565',
        'BORDER_LT':    '#524c8a',
        'BORDER_ACC':   '#a78bfa',
        'TEXT_PRI':     '#f5f3ff',
        'TEXT_SEC':     '#c4b5fd',
        'TEXT_MUT':     '#7c6fcd',
        'ACCENT':       '#a78bfa',
        'ACCENT_DARK':  '#7c3aed',
        'ACCENT_GLOW':  '#ddd6fe',
        'ACCENT_RED':   '#f87171',
        'ACCENT_GOLD':  '#fbbf24',
        'CHART_PALETTE': ['#a78bfa','#818cf8','#c4b5fd','#f472b6',
                          '#38bdf8','#34d399','#fbbf24','#f87171'],
    },
    'sunset': {
        'name':         '🌅 Sunset',
        'BG_DEEP':      '#0f0400',
        'BG_DARK':      '#1a0800',
        'BG_PANEL':     '#2a1200',
        'BG_CARD':      '#391a00',
        'BG_HOVER':     '#4a2200',
        'BG_ACTIVE':    '#5a2900',
        'BORDER':       '#7c3a00',
        'BORDER_LT':    '#a35000',
        'BORDER_ACC':   '#fb923c',
        'TEXT_PRI':     '#fff7ed',
        'TEXT_SEC':     '#fed7aa',
        'TEXT_MUT':     '#c2670f',
        'ACCENT':       '#fb923c',
        'ACCENT_DARK':  '#ea580c',
        'ACCENT_GLOW':  '#fdba74',
        'ACCENT_RED':   '#f87171',
        'ACCENT_GOLD':  '#fbbf24',
        'CHART_PALETTE': ['#fb923c','#fbbf24','#f87171','#a78bfa',
                          '#34d399','#38bdf8','#f472b6','#86efac'],
    },
    'arctic': {
        'name':         '❄️ Arctic',
        'BG_DEEP':      '#dde8f5',
        'BG_DARK':      '#edf3fb',
        'BG_PANEL':     '#dce8f5',
        'BG_CARD':      '#ffffff',
        'BG_HOVER':     '#d0e4f5',
        'BG_ACTIVE':    '#bdd5ef',
        'BORDER':       '#b8cfe8',
        'BORDER_LT':    '#90b5d8',
        'BORDER_ACC':   '#0284c7',
        'TEXT_PRI':     '#0f172a',
        'TEXT_SEC':     '#1e3a5f',
        'TEXT_MUT':     '#475569',
        'ACCENT':       '#0284c7',
        'ACCENT_DARK':  '#0369a1',
        'ACCENT_GLOW':  '#38bdf8',
        'ACCENT_RED':   '#dc2626',
        'ACCENT_GOLD':  '#d97706',
        'CHART_PALETTE': ['#0284c7','#7c3aed','#059669','#d97706',
                          '#dc2626','#0891b2','#9333ea','#16a34a'],
    },
    'slate': {
        'name':         '🔷 Slate',
        'BG_DEEP':      '#0a0e1a',
        'BG_DARK':      '#111827',
        'BG_PANEL':     '#1f2937',
        'BG_CARD':      '#283444',
        'BG_HOVER':     '#374151',
        'BG_ACTIVE':    '#1e3a5f',
        'BORDER':       '#374151',
        'BORDER_LT':    '#4b5563',
        'BORDER_ACC':   '#60a5fa',
        'TEXT_PRI':     '#f9fafb',
        'TEXT_SEC':     '#9ca3af',
        'TEXT_MUT':     '#6b7280',
        'ACCENT':       '#60a5fa',
        'ACCENT_DARK':  '#2563eb',
        'ACCENT_GLOW':  '#93c5fd',
        'ACCENT_RED':   '#f87171',
        'ACCENT_GOLD':  '#fbbf24',
        'CHART_PALETTE': ['#60a5fa','#34d399','#fbbf24','#f87171',
                          '#a78bfa','#38bdf8','#f472b6','#86efac'],
    },
}

# Список тем для выпадающего меню — (id, отображаемое имя)
THEME_LIST = [(k, v['name']) for k, v in THEMES.items()]

# Текущая активная тема
CURRENT_THEME_NAME: str = 'ocean'

# ─── Активные константы (по умолчанию — Ocean) ────────────────────────────────

BG_DEEP     = '#060B18'
BG_DARK     = '#0F172A'
BG_PANEL    = '#1E293B'
BG_CARD     = '#263347'
BG_HOVER    = '#2D3E56'
BG_ACTIVE   = '#1D3A5C'

BORDER      = '#334155'
BORDER_LT   = '#475569'
BORDER_ACC  = '#38BDF8'

TEXT_PRI    = '#F1F5F9'
TEXT_SEC    = '#94A3B8'
TEXT_MUT    = '#64748B'

ACCENT      = '#38BDF8'
ACCENT_DARK = '#0284C7'
ACCENT_GLOW = '#7DD3FC'
ACCENT_RED  = '#F87171'
ACCENT_GOLD = '#FBBF24'

# ─── Eco-специфичные (Volga) ──────────────────────────────────────────────────
VOLGA_DARK  = '#164E63'
VOLGA_MID   = '#0E7490'
VOLGA_LIGHT = '#22D3EE'

# ─── Скругления (не зависят от темы) ─────────────────────────────────────────
RADIUS    = '6px'
RADIUS_SM = '4px'
RADIUS_LG = '10px'

# ─── Палитра графиков ─────────────────────────────────────────────────────────
CHART_PALETTE = [
    '#38BDF8', '#818CF8', '#FBBF24', '#F87171',
    '#34D399', '#A78BFA', '#F472B6', '#4ADE80',
]


# ─── Колбэки смены темы ───────────────────────────────────────────────────────

_theme_callbacks: list = []


def register_theme_callback(cb) -> None:
    """Регистрирует функцию, которая вызывается при каждой смене темы."""
    if cb not in _theme_callbacks:
        _theme_callbacks.append(cb)


def unregister_theme_callback(cb) -> None:
    """Снимает регистрацию колбэка (например при закрытии окна)."""
    try:
        _theme_callbacks.remove(cb)
    except ValueError:
        pass


# ─── Переключение темы ────────────────────────────────────────────────────────

def set_active_theme(name: str) -> None:
    """
    Устанавливает активную тему и обновляет:
    - все модульные константы (BG_*, ACCENT, TEXT_* …)
    - глобальный QSS приложения
    - все зарегистрированные колбэки (окна, которые хотят знать о смене темы)
    """
    global CURRENT_THEME_NAME
    if name not in THEMES:
        return
    CURRENT_THEME_NAME = name
    t = THEMES[name]
    g = globals()
    for key, val in t.items():
        if key != 'name':          # 'name' — отображаемое имя, не цвет
            g[key] = val
    # Refresh Qt app stylesheet
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.setStyleSheet(app_stylesheet())
    except Exception:
        pass
    # Уведомляем все зарегистрированные окна
    for cb in list(_theme_callbacks):
        try:
            cb()
        except Exception:
            pass


# ─── Готовые stylesheet-блоки ─────────────────────────────────────────────────

def scrollbar_style(track=None, handle=None, hover=None):
    """Возвращает QSS для скроллбаров. Параметры читаются из текущей темы."""
    if track  is None: track  = BG_DARK
    if handle is None: handle = BORDER
    if hover  is None: hover  = BORDER_LT
    return f"""
        QScrollBar:vertical {{
            background: {track}; width: 6px; margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {handle}; border-radius: 3px; min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {hover}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{
            background: {track}; height: 6px; margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background: {handle}; border-radius: 3px; min-width: 24px;
        }}
        QScrollBar::handle:horizontal:hover {{ background: {hover}; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    """


def app_stylesheet() -> str:
    """Глобальный стиль всего приложения (читает текущую тему)."""
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
