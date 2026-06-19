from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QVBoxLayout, QWidget


class PlotWidget(QWidget):
    def __init__(self, xlabel: str, ylabel: str, title: str = "", parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(5, 4), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.set_title(title)
        self.ax.grid(True, alpha=0.3)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

    def clear(self):
        self.ax.clear()
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw_idle()

    def plot_xy(self, x, y, label=None, marker="o", linestyle="none", color=None):
        self.ax.plot(x, y, marker=marker, linestyle=linestyle, label=label, color=color, markersize=4)
        if label:
            self.ax.legend(loc="best", fontsize=8)
        self.canvas.draw_idle()

    def set_labels(self, xlabel: str, ylabel: str, title: str = ""):
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.set_title(title)
