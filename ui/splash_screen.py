# ui/splash_screen.py
"""
Экран загрузки (Splash Screen) для EcoLens.

Показывается при старте приложения пока инициализируются модули.
Для использования фонового изображения — положите файл splash.jpg (или .png)
в папку  resources/  рядом с app.py.
"""

import os
from PySide6.QtCore import Qt, QTimer, QRect, QPoint
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import (
    QPainter, QPixmap, QColor, QFont, QLinearGradient,
    QPainterPath, QBrush, QPen, QFontMetrics
)


# ── Цвета в стиле EcoLens ──────────────────────────────────────────────────────
_BG_DARK   = QColor(0x0D, 0x1A, 0x0D)
_GREEN     = QColor(0x4A, 0xDE, 0x80)
_GREEN_DIM = QColor(0x16, 0x6D, 0x34)
_WHITE     = QColor(0xFF, 0xFF, 0xFF)
_GREY      = QColor(0xAA, 0xBB, 0xAA)
_OVERLAY   = QColor(0x00, 0x00, 0x00, 160)   # полупрозрачное затемнение поверх фото

_SPLASH_W = 860
_SPLASH_H = 520

# Шаги загрузки: (текст, значение прогресса 0-100)
LOAD_STEPS = [
    ("Инициализация приложения…",         10),
    ("Загрузка UI-модулей…",              30),
    ("Подготовка компонентов дашборда…",  55),
    ("Создание главного окна…",           80),
    ("Запуск…",                           100),
]


class SplashScreen(QWidget):
    """
    Полноэкранный splash screen с фоновой картинкой, прогресс-баром и
    статус-текстом.

    Использование:
        splash = SplashScreen()
        splash.show()
        splash.set_progress(30, "Загрузка модулей…")
        ...
        splash.finish(main_window)   # плавно исчезает и показывает main_window
    """

    def __init__(self, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setFixedSize(_SPLASH_W, _SPLASH_H)

        self._progress  = 0          # 0..100
        self._status    = "Запуск…"
        self._bg_pixmap = self._load_background()
        self._opacity   = 1.0        # для fade-out
        self._fade_timer = None

        # Центрируем на экране
        screen = QApplication.primaryScreen()
        if screen:
            sr = screen.availableGeometry()
            self.move(
                sr.x() + (sr.width()  - _SPLASH_W) // 2,
                sr.y() + (sr.height() - _SPLASH_H) // 2,
            )

    # ── Публичное API ──────────────────────────────────────────────────────────

    def set_progress(self, value: int, status: str = ""):
        """Обновляет прогресс-бар и статус-текст; вызывайте между шагами загрузки."""
        self._progress = max(0, min(100, value))
        if status:
            self._status = status
        self.repaint()
        QApplication.processEvents()

    def finish(self, main_window=None):
        """Плавно закрывает сплеш и показывает главное окно."""
        if main_window is not None:
            self._main_window = main_window
        else:
            self._main_window = None

        self._fade_step = 0
        self._fade_timer = QTimer(self)
        self._fade_timer.timeout.connect(self._do_fade)
        self._fade_timer.start(16)   # ~60 fps

    # ── Внутренняя логика ──────────────────────────────────────────────────────

    def _load_background(self) -> QPixmap | None:
        """
        Ищет фоновое изображение для сплеша.
        Порядок поиска:
          1. EcoLens_VarC.*  в корне проекта (DashboardBuilder/)
          2. EcoLens_VarC.*  в папке resources/
          3. splash.*        в корне проекта
          4. splash.*        в папке resources/
        """
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resources = os.path.join(base, "resources")
        exts = (".jpg", ".jpeg", ".png", ".webp", ".bmp")

        search = [
            (base,      "ecolens_variantC_noX"),
            (base,      "EcoLens_VarC"),
            (resources, "ecolens_variantC_noX"),
            (resources, "EcoLens_VarC"),
            (base,      "splash"),
            (resources, "splash"),
        ]
        for folder, stem in search:
            for ext in exts:
                path = os.path.join(folder, stem + ext)
                if os.path.isfile(path):
                    pix = QPixmap(path)
                    if not pix.isNull():
                        return pix.scaled(
                            _SPLASH_W, _SPLASH_H,
                            Qt.KeepAspectRatioByExpanding,
                            Qt.SmoothTransformation
                        )
        return None

    def _do_fade(self):
        self._fade_step += 1
        steps = 20
        self._opacity = max(0.0, 1.0 - self._fade_step / steps)
        self.repaint()
        QApplication.processEvents()
        if self._fade_step >= steps:
            self._fade_timer.stop()
            if self._main_window is not None:
                self._main_window.show()
            self.close()

    # ── Рисование ─────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setOpacity(self._opacity)

        W, H = self.width(), self.height()

        # 1. Фоновое изображение или градиент
        if self._bg_pixmap:
            # Центрируем кроп, если картинка шире/выше окна
            src = self._bg_pixmap
            sx = (src.width()  - W) // 2
            sy = (src.height() - H) // 2
            p.drawPixmap(0, 0, src, max(0, sx), max(0, sy), W, H)
        else:
            # Градиент-заглушка если картинки нет
            grad = QLinearGradient(0, 0, 0, H)
            grad.setColorAt(0.0, QColor(0x0A, 0x1F, 0x0A))
            grad.setColorAt(0.5, QColor(0x0D, 0x2B, 0x0D))
            grad.setColorAt(1.0, QColor(0x05, 0x10, 0x05))
            p.fillRect(0, 0, W, H, grad)

        # 2. Затемняющий оверлей (усиливаем внизу для читаемости текста)
        overlay_grad = QLinearGradient(0, 0, 0, H)
        overlay_grad.setColorAt(0.0, QColor(0, 0, 0, 80))
        overlay_grad.setColorAt(0.45, QColor(0, 0, 0, 110))
        overlay_grad.setColorAt(1.0, QColor(0, 0, 0, 210))
        p.fillRect(0, 0, W, H, overlay_grad)

        # 3. Зелёная горизонтальная полоска сверху
        p.fillRect(0, 0, W, 4, _GREEN)

        # 4. Центральный блок с логотипом ─────────────────────────────────────
        center_y = int(H * 0.38)

        # Тонкая разделительная линия
        line_y = center_y + 10
        pen = QPen(QColor(0xFF, 0xFF, 0xFF, 40))
        pen.setWidth(1)
        p.setPen(pen)
        p.drawLine(W // 4, line_y, 3 * W // 4, line_y)

        # 5. Нижняя панель: прогресс-бар + статус ────────────────────────────
        bar_h    = 6
        bar_y    = H - 54
        bar_x    = 60
        bar_w    = W - 120
        radius   = bar_h // 2

        # Трек
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0xFF, 0xFF, 0xFF, 30))
        track_path = QPainterPath()
        track_path.addRoundedRect(bar_x, bar_y, bar_w, bar_h, radius, radius)
        p.drawPath(track_path)

        # Заполненная часть
        fill_w = int(bar_w * self._progress / 100)
        if fill_w > 0:
            fill_grad = QLinearGradient(bar_x, 0, bar_x + fill_w, 0)
            fill_grad.setColorAt(0.0, _GREEN_DIM)
            fill_grad.setColorAt(1.0, _GREEN)
            p.setBrush(QBrush(fill_grad))
            fill_path = QPainterPath()
            fill_path.addRoundedRect(bar_x, bar_y, fill_w, bar_h, radius, radius)
            p.drawPath(fill_path)

            # Светящийся кончик
            if fill_w > 6:
                glow_x = bar_x + fill_w - 3
                glow_grad = QLinearGradient(glow_x - 10, 0, glow_x + 4, 0)
                glow_grad.setColorAt(0.0, QColor(0x4A, 0xDE, 0x80, 0))
                glow_grad.setColorAt(1.0, QColor(0x86, 0xFF, 0xB0, 200))
                p.setBrush(QBrush(glow_grad))
                p.drawRect(glow_x - 10, bar_y - 2, 14, bar_h + 4)

        # Процент справа
        pct_font = QFont("Segoe UI", 11, QFont.Bold)
        p.setFont(pct_font)
        p.setPen(_GREEN)
        pct_rect = QRect(W - 58, bar_y - 2, 48, bar_h + 4)
        p.drawText(pct_rect, Qt.AlignRight | Qt.AlignVCenter,
                   f"{self._progress}%")

        # Статус-текст
        st_font = QFont("Segoe UI", 10)
        p.setFont(st_font)
        p.setPen(QColor(0xCC, 0xDD, 0xCC, 200))
        st_rect = QRect(bar_x, bar_y + bar_h + 8, bar_w, 20)
        p.drawText(st_rect, Qt.AlignLeft | Qt.AlignVCenter, self._status)

        # Версия / копирайт справа внизу
        ver_font = QFont("Segoe UI", 9)
        p.setFont(ver_font)
        p.setPen(QColor(0xAA, 0xAA, 0xAA, 120))
        p.drawText(QRect(0, H - 22, W - 12, 18),
                   Qt.AlignRight | Qt.AlignVCenter,
                   "© ГБУ НО «Экология региона»  ·  Княгининский университет")

        p.end()
