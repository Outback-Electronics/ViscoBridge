"""Printable HTML report generation (sample/method info, data table, flow
curve chart, and fit results) — opens cleanly in any browser's print dialog."""
from __future__ import annotations

import base64
import io
from html import escape

import matplotlib.pyplot as plt

from viscobridge.analysis import FitResult
from viscobridge.models import Run


def _chart_png_base64(run: Run) -> str:
    fig, ax = plt.subplots(figsize=(6, 4))
    gamma = [p.shear_rate for p in run.points]
    visc = [p.viscosity_cp for p in run.points]
    ax.plot(gamma, visc, "o-", markersize=4)
    ax.set_xlabel("Shear Rate (1/s)")
    ax.set_ylabel("Viscosity (cP)")
    ax.set_title("Viscosity vs Shear Rate")
    ax.grid(True, alpha=0.3)
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def generate_html_report(run: Run, path: str, fit_result: FitResult | None = None) -> None:
    img_b64 = _chart_png_base64(run) if run.points else ""

    rows = "".join(
        f"<tr><td>{p.t_s:.2f}</td><td>{p.rpm:.2f}</td><td>{p.torque_pct:.2f}</td>"
        f"<td>{p.temp_c:.2f}</td><td>{p.shear_rate:.2f}</td><td>{p.shear_stress:.2f}</td>"
        f"<td>{p.viscosity_cp:.2f}</td></tr>"
        for p in run.points
    )

    fit_html = ""
    if fit_result is not None:
        param_rows = "".join(
            f"<tr><td>{escape(name)}</td><td>{val:.4g}</td></tr>"
            for name, val in zip(fit_result.param_names, fit_result.params)
        )
        fit_html = f"""
        <h2>Flow Curve Fit</h2>
        <p>Model: {escape(fit_result.model_name)} &mdash; R&sup2; = {fit_result.r_squared:.4f}</p>
        <table><tr><th>Parameter</th><th>Value</th></tr>{param_rows}</table>
        """

    steps_html = "".join(
        f"<tr><td>{escape(s.step_type)}</td><td>{s.start_speed_rpm:.2f}</td>"
        f"<td>{s.end_speed_rpm:.2f}</td><td>{s.duration_s:.1f}</td>"
        f"<td>{s.interval_s:.2f}</td><td>{s.target_temp_c:.1f}</td></tr>"
        for s in run.method.steps
    )

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>ViscoBridge Report - {escape(run.sample.name)}</title>
<style>
  body {{ font-family: sans-serif; margin: 2em; color: #222; }}
  h1, h2 {{ border-bottom: 1px solid #ccc; padding-bottom: 0.2em; }}
  table {{ border-collapse: collapse; margin-bottom: 1.5em; }}
  th, td {{ border: 1px solid #ccc; padding: 4px 8px; font-size: 0.9em; }}
  th {{ background: #f0f0f0; }}
  img {{ max-width: 100%; }}
</style>
</head>
<body>
  <h1>ViscoBridge Test Report</h1>
  <table>
    <tr><th>Sample</th><td>{escape(run.sample.name)}</td></tr>
    <tr><th>Operator</th><td>{escape(run.sample.operator)}</td></tr>
    <tr><th>Notes</th><td>{escape(run.sample.notes)}</td></tr>
    <tr><th>Timestamp</th><td>{escape(run.timestamp)}</td></tr>
    <tr><th>Method</th><td>{escape(run.method.name)}</td></tr>
    <tr><th>Instrument model</th><td>{escape(run.method.instrument_model.name)}</td></tr>
    <tr><th>Spindle</th><td>{escape(run.method.spindle.name)} (SMC={run.method.spindle.smc}, SRC={run.method.spindle.src})</td></tr>
    <tr><th>Container</th><td>{escape(run.method.container)}</td></tr>
  </table>

  <h2>Test Steps</h2>
  <table>
    <tr><th>Step Type</th><th>Start RPM</th><th>End RPM</th><th>Duration (s)</th><th>Interval (s)</th><th>Target Temp (C)</th></tr>
    {steps_html}
  </table>

  <h2>Flow Curve</h2>
  <img src="data:image/png;base64,{img_b64}" alt="Viscosity vs Shear Rate">

  {fit_html}

  <h2>Data</h2>
  <table>
    <tr><th>Time (s)</th><th>RPM</th><th>Torque (%)</th><th>Temp (C)</th>
        <th>Shear Rate (1/s)</th><th>Shear Stress (dyne/cm^2)</th><th>Viscosity (cP)</th></tr>
    {rows}
  </table>
</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
