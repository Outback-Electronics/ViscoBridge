from __future__ import annotations

import numpy as np
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from viscobridge import analysis
from viscobridge.ui.plot_widget import PlotWidget


class FitDialog(QDialog):
    def __init__(self, shear_rate: np.ndarray, shear_stress: np.ndarray, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Flow Curve Model Fit")
        self.resize(700, 550)
        self.shear_rate = shear_rate
        self.shear_stress = shear_stress
        self.last_result = None

        layout = QVBoxLayout(self)
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(list(analysis.MODELS.keys()))
        top_row.addWidget(self.model_combo)
        fit_btn = QPushButton("Fit")
        fit_btn.clicked.connect(self.run_fit)
        top_row.addWidget(fit_btn)
        top_row.addStretch()
        layout.addLayout(top_row)

        self.plot = PlotWidget("Shear Rate (1/s)", "Shear Stress (dyne/cm^2)", "Flow Curve")
        layout.addWidget(self.plot)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(120)
        layout.addWidget(self.result_text)

        self._plot_raw()

    def _plot_raw(self):
        self.plot.clear()
        self.plot.plot_xy(self.shear_rate, self.shear_stress, label="Data", marker="o", linestyle="none")

    def run_fit(self):
        model_name = self.model_combo.currentText()
        try:
            result = analysis.fit_model(model_name, self.shear_rate, self.shear_stress)
        except Exception as exc:
            self.result_text.setPlainText(f"Fit failed: {exc}")
            return

        self.last_result = result
        self._plot_raw()
        gamma_smooth = np.linspace(max(self.shear_rate.min(), 1e-6), self.shear_rate.max(), 200)
        tau_pred = analysis.predict(model_name, result.params, gamma_smooth)
        self.plot.plot_xy(gamma_smooth, tau_pred, label=f"{model_name} fit", marker="none", linestyle="-")

        self.result_text.setPlainText(str(result))
