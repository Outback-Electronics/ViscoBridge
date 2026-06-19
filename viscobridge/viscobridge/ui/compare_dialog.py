from __future__ import annotations

from scipy.stats import f_oneway
from PySide6.QtWidgets import QDialog, QFileDialog, QLabel, QMessageBox, QVBoxLayout

from viscobridge import io_utils
from viscobridge.ui.plot_widget import PlotWidget


class CompareDialog(QDialog):
    """Overlay viscosity-vs-shear-rate curves from several saved runs and
    run a one-way ANOVA across their viscosity distributions to test
    whether the samples/batches differ significantly."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Compare Runs")
        self.resize(800, 650)

        layout = QVBoxLayout(self)
        self.plot = PlotWidget("Shear Rate (1/s)", "Viscosity (cP)", "Run Comparison")
        layout.addWidget(self.plot)

        self.stats_label = QLabel("")
        self.stats_label.setWordWrap(True)
        layout.addWidget(self.stats_label)

        self._load_runs()

    def _load_runs(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Runs to Compare", filter="ViscoBridge Run (*.vbr)")
        if not paths:
            self.reject()
            return

        groups = []
        labels = []
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
            groups.append(visc)
            labels.append(label)

        self._show_stats(groups, labels)

    def _show_stats(self, groups: list[list[float]], labels: list[str]):
        if len(groups) < 2 or any(len(g) < 2 for g in groups):
            self.stats_label.setText("Load at least two runs (each with 2+ points) for statistical comparison.")
            return

        means = [sum(g) / len(g) for g in groups]
        mean_lines = "; ".join(f"{label}: mean viscosity = {mean:.2f} cP" for label, mean in zip(labels, means))
        f_stat, p_value = f_oneway(*groups)
        verdict = (
            "significantly different (p < 0.05)" if p_value < 0.05
            else "not significantly different (p >= 0.05)"
        )
        self.stats_label.setText(
            f"{mean_lines}\n"
            f"One-way ANOVA across runs: F = {f_stat:.3f}, p = {p_value:.4g} -- viscosity is {verdict}."
        )
