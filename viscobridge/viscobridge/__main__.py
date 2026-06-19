import sys
from importlib import resources

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from viscobridge.ui.main_window import MainWindow


def _app_icon() -> QIcon:
    icon_name = "icon.ico" if sys.platform == "win32" else "icon.png"
    path = resources.files("viscobridge.resources").joinpath(icon_name)
    return QIcon(str(path))


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ViscoBridge")
    app.setOrganizationName("ViscoBridge")
    icon = _app_icon()
    app.setWindowIcon(icon)
    window = MainWindow()
    window.setWindowIcon(icon)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
