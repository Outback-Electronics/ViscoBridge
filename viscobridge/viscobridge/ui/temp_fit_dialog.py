from __future__ import annotations

import numpy as np
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
)

from viscobridge import analysis
from viscobridge.ui.plot_widget import PlotWidget


class TempFitDialog(QDialog):
    """Fits Arrhenius or WLF temperature-dependence models to viscosity vs.
    temperature data (e.g. from a Temperature Sweep test)."""

    def __init__(self, temp_c: np.ndarray, viscosity: np.ndarray, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Temperature Dependence Fit")
        self.resize(750, 600)
        self.temp_c = temp_c
        self.viscosity = viscosity
        self.last_result = None

        layout = QVBoxLayout(self)
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(list(analysis.TEMP_MODELS.keys()))
        top_row.addWidget(self.model_combo)
        fit_btn = QPushButton("Fit")
        fit_btn.clicked.connect(self.run_fit)
        top_row.addWidget(fit_btn)
        top_row.addStretch()
        layout.addLayout(top_row)

        tabs = QTabWidget()
        self.plot = PlotWidget("Temperature (C)", "Viscosity (cP)", "Viscosity vs Temperature")
        self.residual_plot = PlotWidget("Temperature (C)", "Residual (cP)", "Fit Residuals")
        tabs.addTab(self.plot, "Viscosity vs Temperature")
        tabs.addTab(self.residual_plot, "Residuals")
        layout.addWidget(tabs)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(140)
        layout.addWidget(self.result_text)

        self._plot_raw()

    def _plot_raw(self):
        self.plot.clear()
        self.plot.plot_xy(self.temp_c, self.viscosity, label="Data", marker="o", linestyle="none")
        self.residual_plot.clear()

    def run_fit(self):
        model_name = self.model_combo.currentText()
        try:
            result = analysis.fit_temperature_model(model_name, self.temp_c, self.viscosity)
        except Exception as exc:
            self.result_text.setPlainText(f"Fit failed: {exc}")
            return

        self.last_result = result
        self._plot_raw()
        temp_smooth = np.linspace(self.temp_c.min(), self.temp_c.max(), 200)
        visc_pred = analysis.predict_temperature(model_name, result.params, temp_smooth)
        self.plot.plot_xy(temp_smooth, visc_pred, label=f"{model_name} fit", marker="none", linestyle="-")

        self.residual_plot.clear()
        self.residual_plot.ax.axhline(0, color="gray", linewidth=0.8)
        self.residual_plot.plot_xy(result.x, result.residuals, label="Residual", marker="o", linestyle="none")

        self.result_text.setPlainText(str(result))
