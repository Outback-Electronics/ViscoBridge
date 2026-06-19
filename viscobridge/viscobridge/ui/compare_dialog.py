from __future__ import annotations

from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox, QVBoxLayout

from viscobridge import io_utils
from viscobridge.ui.plot_widget import PlotWidget


class CompareDialog(QDialog):
    """Overlay viscosity-vs-shear-rate curves from several saved runs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Compare Runs")
        self.resize(800, 600)

        layout = QVBoxLayout(self)
        self.plot = PlotWidget("Shear Rate (1/s)", "Viscosity (cP)", "Run Comparison")
        layout.addWidget(self.plot)

        self._load_runs()

    def _load_runs(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Runs to Compare", filter="ViscoBridge Run (*.vbr)")
        if not paths:
            self.reject()
            return

        for path in paths:
            try:
                run = io_utils.load_run(path)
            except Exception as exc:
                QMessageBox.warning(self, "Load failed", f"Could not load {path}:\n{exc}")
                continue
            if not run.points:
                continue
            gamma = [p.shear_rate for p in run.points]
            visc = [p.viscosity_cp for p in run.points]
            label = run.sample.name or path
            self.plot.plot_xy(gamma, visc, label=label, marker="o", linestyle="-")
