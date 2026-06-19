from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QVBoxLayout, QWidget

# mplot3d must be imported explicitly to register the "3d" projection with
# matplotlib's projection registry -- relying on matplotlib to pull it in
# implicitly breaks when multiple matplotlib installs are on the path
# (e.g. a system apt package shadowing/shadowed-by a pip install). This
# import itself can fail (not just register-and-fail) when the mpl_toolkits
# found on the path is a different, incompatible version from the
# matplotlib core that got imported -- caught here, at import time, so a
# broken environment doesn't take down the whole application at startup;
# the error only surfaces when a 3D widget is actually requested.
try:
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    _MPLOT3D_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # noqa: BLE001 - want to defer *any* import failure
    _MPLOT3D_IMPORT_ERROR = exc

_MPLOT3D_HELP = (
    "matplotlib's 3D toolkit (mplot3d) isn't available or is broken in this "
    "environment. This usually means two conflicting matplotlib installations "
    "are on your Python path (e.g. an apt 'python3-matplotlib' package and a "
    "pip-installed matplotlib under ~/.local) with mismatched versions of "
    "matplotlib core and mpl_toolkits. Run `pip show matplotlib` and "
    "`apt list --installed | grep matplotlib` to check; removing the apt "
    "package (sudo apt remove python3-matplotlib) and keeping only the pip "
    "install usually fixes it."
)


class Plot3DWidget(QWidget):
    """A 3D matplotlib canvas (mplot3d) for surfaces, scatter clouds, and
    parametric lines -- shares the same embed pattern as PlotWidget."""

    def __init__(self, xlabel: str, ylabel: str, zlabel: str, title: str = "", parent=None):
        super().__init__(parent)
        if _MPLOT3D_IMPORT_ERROR is not None:
            raise RuntimeError(_MPLOT3D_HELP) from _MPLOT3D_IMPORT_ERROR
        self.figure = Figure(figsize=(6, 5), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        try:
            self.ax = self.figure.add_subplot(111, projection="3d")
        except ValueError as exc:
            raise RuntimeError(_MPLOT3D_HELP) from exc
        self.set_labels(xlabel, ylabel, zlabel, title)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    def clear(self):
        self.ax.clear()
        self.canvas.draw_idle()

    def set_labels(self, xlabel: str, ylabel: str, zlabel: str, title: str = ""):
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.set_zlabel(zlabel)
        self.ax.set_title(title)

    def scatter(self, x, y, z, label=None, color=None):
        self.ax.scatter(x, y, z, label=label, color=color, s=20)
        if label:
            self.ax.legend(loc="best", fontsize=8)
        self.canvas.draw_idle()

    def surface(self, x_grid, y_grid, z_grid, cmap="viridis", alpha=0.7):
        self.ax.plot_surface(x_grid, y_grid, z_grid, cmap=cmap, alpha=alpha, linewidth=0, antialiased=True)
        self.canvas.draw_idle()

    def wireframe(self, x_grid, y_grid, z_grid, color="gray"):
        self.ax.plot_wireframe(x_grid, y_grid, z_grid, color=color, linewidth=0.5, alpha=0.6)
        self.canvas.draw_idle()

    def line(self, x, y, z, label=None, color=None):
        self.ax.plot(x, y, z, label=label, color=color, marker="o", markersize=3)
        if label:
            self.ax.legend(loc="best", fontsize=8)
        self.canvas.draw_idle()
