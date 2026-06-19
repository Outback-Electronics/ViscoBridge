from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from rheocalc32.instruments import InstrumentDriver, InstrumentError

# How far the average/peak torque reading may stray from 0% with nothing
# mounted before we call the zero calibration suspect.
TORQUE_TOLERANCE_PCT = 2.0


class CalibrationDialog(QDialog):
    """Runs the instrument unloaded (no spindle, nothing immersed) for a
    fixed duration and checks that torque stays at ~0%, to verify the
    zero calibration taken at connect time is still good."""

    def __init__(self, instrument: InstrumentDriver, duration_s: float = 30.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calibration Check")
        self.instrument = instrument
        self.duration_s = duration_s
        self.interval_s = 0.5
        self.elapsed_s = 0.0
        self.readings: list[float] = []

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Remove the spindle (nothing mounted, nothing immersed) and\n"
            f"click Start. The motor will run unloaded for {int(duration_s)}s;\n"
            "torque should read ~0% the whole time."
        ))
        self.status_label = QLabel("Ready.")
        layout.addWidget(self.status_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, int(round(duration_s / self.interval_s)))
        layout.addWidget(self.progress)

        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self._start)
        layout.addWidget(self.start_btn)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self._on_close)
        buttons.button(QDialogButtonBox.Close).clicked.connect(self._on_close)
        layout.addWidget(buttons)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    def _start(self):
        self.start_btn.setEnabled(False)
        self.readings.clear()
        self.elapsed_s = 0.0
        self.progress.setValue(0)
        try:
            self.instrument.set_speed(0.0)
        except InstrumentError as exc:
            self.status_label.setText(f"Failed to start motor: {exc}")
            self.start_btn.setEnabled(True)
            return
        self.status_label.setText("Running...")
        self.timer.start(int(self.interval_s * 1000))

    def _tick(self):
        try:
            _rpm, torque_pct, _temp_c = self.instrument.read()
        except InstrumentError as exc:
            self.timer.stop()
            self.status_label.setText(f"Instrument error: {exc}")
            self.start_btn.setEnabled(True)
            return

        self.readings.append(torque_pct)
        self.elapsed_s += self.interval_s
        self.progress.setValue(min(self.progress.maximum(), int(round(self.elapsed_s / self.interval_s))))
        self.status_label.setText(f"Running... torque = {torque_pct:.2f}%  ({self.elapsed_s:.0f}s)")

        if self.elapsed_s >= self.duration_s:
            self.timer.stop()
            self._finish()

    def _finish(self):
        try:
            self.instrument.set_speed(0.0)
        except InstrumentError:
            pass
        if not self.readings:
            self.status_label.setText("No readings collected.")
            self.start_btn.setEnabled(True)
            return

        avg = sum(self.readings) / len(self.readings)
        peak = max(abs(r) for r in self.readings)
        if peak <= TORQUE_TOLERANCE_PCT:
            self.status_label.setText(
                f"PASS: avg torque {avg:.2f}%, peak |torque| {peak:.2f}% "
                f"(within +/-{TORQUE_TOLERANCE_PCT:.0f}% of zero)."
            )
        else:
            self.status_label.setText(
                f"FAIL: avg torque {avg:.2f}%, peak |torque| {peak:.2f}% "
                f"exceeds +/-{TORQUE_TOLERANCE_PCT:.0f}% of zero. "
                "Re-zero (reconnect) and check for spindle/debris/friction."
            )
        self.start_btn.setEnabled(True)

    def _on_close(self):
        self.timer.stop()
        self.reject()
