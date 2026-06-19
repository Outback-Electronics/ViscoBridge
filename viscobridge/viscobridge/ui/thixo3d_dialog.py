from __future__ import annotations

import numpy as np
from PySide6.QtWidgets import QDialog, QVBoxLayout

from viscobridge.models import Run
from viscobridge.ui.plot3d_widget import Plot3DWidget


class Thixo3DDialog(QDialog):
    """Plots a run's (shear rate, shear stress, time) trajectory in 3D so
    time-dependent/thixotropic hysteresis -- e.g. a Thixotropic Index
    Up-Down test -- is visible as a loop rather than two overlapping 2D
    traces."""

    def __init__(self, run: Run, parent=None):
        super().__init__(parent)
        self.setWindowTitle("3D Thixotropy Loop")
        self.resize(800, 650)

        layout = QVBoxLayout(self)
        self.plot = Plot3DWidget("Shear Rate (1/s)", "Shear Stress (dyne/cm^2)", "Time (s)",
                                  "Shear Rate / Stress / Time Trajectory")
        layout.addWidget(self.plot)

        gamma = np.array([p.shear_rate for p in run.points])
        tau = np.array([p.shear_stress for p in run.points])
        t = np.array([p.t_s for p in run.points])
        self.plot.line(gamma, tau, t, label=run.sample.name or "Run", color="tab:blue")
