"""Canned test-step templates (RheoCalc-style "Test Wizard" presets)."""
from __future__ import annotations

from viscobridge.models import TestStep

TEST_TEMPLATES: dict[str, list[TestStep]] = {
    "Flow Curve (Speed Ramp)": [
        TestStep("Speed Ramp", 1.0, 100.0, 60.0, 1.0, 25.0),
    ],
    "Thixotropic Index (Up-Down)": [
        TestStep("Speed Hold", 5.0, 5.0, 30.0, 1.0, 25.0),
        TestStep("Speed Hold", 50.0, 50.0, 30.0, 1.0, 25.0),
        TestStep("Speed Hold", 5.0, 5.0, 30.0, 1.0, 25.0),
    ],
    "Temperature Sweep": [
        TestStep("Temperature Ramp", 50.0, 50.0, 60.0, 2.0, 25.0),
        TestStep("Temperature Ramp", 50.0, 50.0, 60.0, 2.0, 40.0),
        TestStep("Temperature Ramp", 50.0, 50.0, 60.0, 2.0, 60.0),
        TestStep("Temperature Ramp", 50.0, 50.0, 60.0, 2.0, 80.0),
    ],
    "Time Hold (Stability Check)": [
        TestStep("Time Hold", 30.0, 30.0, 300.0, 5.0, 25.0),
    ],
}
