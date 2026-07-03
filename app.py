import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt


def main():
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

    # ── Splash screen ──────────────────────────────────────────────────────────
    from ui.splash_screen import SplashScreen, LOAD_STEPS
    splash = SplashScreen()
    splash.show()
    splash.set_progress(LOAD_STEPS[0][1], LOAD_STEPS[0][0])

    # ── Шаг 1: загружаем тему ─────────────────────────────────────────────────
    from ui import theme  # noqa: F401 — просто прогреваем импорт
    splash.set_progress(LOAD_STEPS[1][1], LOAD_STEPS[1][0])

    # ── Шаг 2: загружаем тяжёлые UI-модули ───────────────────────────────────
    from ui.start_screen import StartScreen          # noqa: F401
    from ui.eco_dashboard_window import EcoDashboardWindow  # noqa: F401
    from ui.configurator_window import ConfiguratorWindow   # noqa: F401
    splash.set_progress(LOAD_STEPS[2][1], LOAD_STEPS[2][0])

    # ── Шаг 3: создаём главное окно ───────────────────────────────────────────
    from ui.main_window import MainWindow
    splash.set_progress(LOAD_STEPS[3][1], LOAD_STEPS[3][0])
    window = MainWindow()

    # ── Шаг 4: готово ─────────────────────────────────────────────────────────
    splash.set_progress(LOAD_STEPS[4][1], LOAD_STEPS[4][0])
    splash.finish(window)   # плавно закрывает сплеш и показывает окно

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
