from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QVBoxLayout, QWidget


class Plot3DWidget(QWidget):
    """A 3D matplotlib canvas (mplot3d) for surfaces, scatter clouds, and
    parametric lines -- shares the same embed pattern as PlotWidget."""

    def __init__(self, xlabel: str, ylabel: str, zlabel: str, title: str = "", parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(6, 5), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111, projection="3d")
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
