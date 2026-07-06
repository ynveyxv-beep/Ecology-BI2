import sys

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    import traceback
    def _excepthook(exc_type, exc_value, exc_tb):
        from PySide6.QtWidgets import QMessageBox
        msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        QMessageBox.critical(None, "Критическая ошибка", msg[:2000])
    sys.excepthook = _excepthook

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()