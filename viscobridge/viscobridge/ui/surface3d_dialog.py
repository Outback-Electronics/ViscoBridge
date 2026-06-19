from __future__ import annotations

import numpy as np
from PySide6.QtWidgets import QDialog, QFileDialog, QLabel, QMessageBox, QVBoxLayout
from scipy.interpolate import griddata

from viscobridge import io_utils
from viscobridge.ui.plot3d_widget import Plot3DWidget


class Surface3DDialog(QDialog):
    """Combines multiple saved runs (e.g. flow curves captured at several
    temperatures) into one 3D viscosity vs. shear-rate vs. temperature
    surface, interpolated across the loaded data -- something neither
    RheoCalc32 nor RheocalcT offers."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("3D Viscosity Surface (Shear Rate vs Temperature)")
        self.resize(800, 650)

        layout = QVBoxLayout(self)
        self.plot = Plot3DWidget("Shear Rate (1/s)", "Temperature (C)", "Viscosity (cP)",
                                  "Viscosity Surface")
        layout.addWidget(self.plot)
        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self._load_runs()

    def _load_runs(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Runs (ideally at different temperatures/shear rates)", filter="ViscoBridge Run (*.vbr)"
        )
        if not paths:
            self.reject()
            return

        gamma_all, temp_all, visc_all = [], [], []
        for path in paths:
            try:
                run = io_utils.load_run(path)
            except Exception as exc:
                QMessageBox.warning(self, "Load failed", f"Could not load {path}:\n{exc}")
                continue
            for p in run.points:
                if p.shear_rate > 0 and p.viscosity_cp > 0:
                    gamma_all.append(p.shear_rate)
                    temp_all.append(p.temp_c)
                    visc_all.append(p.viscosity_cp)

        if len(gamma_all) < 4:
            self.info_label.setText("Not enough data points (with nonzero shear rate) across the loaded runs to build a surface.")
            return

        gamma_all = np.array(gamma_all)
        temp_all = np.array(temp_all)
        visc_all = np.array(visc_all)

        self.plot.scatter(gamma_all, temp_all, visc_all, label="Data", color="black")

        if np.ptp(temp_all) < 1e-6 or np.ptp(gamma_all) < 1e-6:
            self.info_label.setText(
                "Loaded data only spans one shear rate or one temperature -- "
                "showing raw points only (need both axes to vary for a surface)."
            )
            return

        grid_gamma, grid_temp = np.meshgrid(
            np.linspace(gamma_all.min(), gamma_all.max(), 40),
            np.linspace(temp_all.min(), temp_all.max(), 40),
        )
        grid_visc = griddata((gamma_all, temp_all), visc_all, (grid_gamma, grid_temp), method="linear")
        self.plot.surface(grid_gamma, grid_temp, grid_visc)
        self.info_label.setText(f"Surface interpolated (linear) from {len(gamma_all)} data points across {len(paths)} run(s).")
