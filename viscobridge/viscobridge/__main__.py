import sys

from PySide6.QtWidgets import QApplication

from viscobridge.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ViscoBridge")
    app.setOrganizationName("ViscoBridge")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
