from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QVBoxLayout, QWidget

# mplot3d must be imported explicitly to register the "3d" projection with
# matplotlib's projection registry -- relying on matplotlib to pull it in
# implicitly breaks when multiple matplotlib installs are on the path
# (e.g. a system apt package shadowing/shadowed-by a pip install), which
# can silently leave the registry without "3d".
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401


class Plot3DWidget(QWidget):
    """A 3D matplotlib canvas (mplot3d) for surfaces, scatter clouds, and
    parametric lines -- shares the same embed pattern as PlotWidget."""

    def __init__(self, xlabel: str, ylabel: str, zlabel: str, title: str = "", parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(6, 5), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        try:
            self.ax = self.figure.add_subplot(111, projection="3d")
        except ValueError as exc:
            raise RuntimeError(
                "matplotlib's 3D toolkit (mplot3d) isn't available. This usually "
                "means two conflicting matplotlib installations are on your "
                "Python path (e.g. an apt 'python3-matplotlib' package and a "
                "pip-installed matplotlib under ~/.local). Run "
                "`pip show matplotlib` and `apt list --installed | grep matplotlib` "
                "to check, and keep only one (pip install --user --force-reinstall "
                "matplotlib is usually the fix)."
            ) from exc
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
