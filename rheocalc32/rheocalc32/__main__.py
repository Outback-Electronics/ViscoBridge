import sys

from PySide6.QtWidgets import QApplication

from rheocalc32.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("RheoCalc32")
    app.setOrganizationName("RheoCalc32")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
