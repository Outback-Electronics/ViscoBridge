from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from viscobridge.constants import DEFAULT_SPINDLES, INSTRUMENT_MODELS, InstrumentModel, Spindle


@dataclass
class TestStep:
    step_type: str = "Speed Ramp"
    start_speed_rpm: float = 1.0
    end_speed_rpm: float = 100.0
    duration_s: float = 60.0
    interval_s: float = 1.0
    target_temp_c: float = 25.0


@dataclass
class Sample:
    name: str = "Sample 1"
    operator: str = ""
    notes: str = ""


@dataclass
class TestMethod:
    name: str = "New Method"
    instrument_model: InstrumentModel = field(default_factory=lambda: INSTRUMENT_MODELS[5])  # DV3TRV
    spindle: Spindle = field(default_factory=lambda: DEFAULT_SPINDLES[0])
    container: str = "600 mL Beaker"
    steps: list[TestStep] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "TestMethod":
        spindle = Spindle(**d["spindle"])
        instrument_model = InstrumentModel(**d["instrument_model"])
        steps = [TestStep(**s) for s in d["steps"]]
        return cls(name=d["name"], instrument_model=instrument_model, spindle=spindle,
                   container=d.get("container", ""), steps=steps)


@dataclass
class DataPoint:
    t_s: float
    rpm: float
    torque_pct: float
    temp_c: float
    shear_rate: float
    shear_stress: float
    viscosity_cp: float


@dataclass
class Run:
    method: TestMethod
    sample: Sample
    timestamp: str
    points: list[DataPoint] = field(default_factory=list)
    # Traceability: which physical instrument produced this data, the
    # torque-transducer zero offset it was calibrated with at connect
    # time, and the most recent unloaded calibration-check result before
    # this run -- needed for audit trails (e.g. ISO/GxP lab compliance).
    instrument_id: str = ""
    zero_offset_counts: int | None = None
    calibration_check: dict | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "method": self.method.to_dict(),
                "sample": asdict(self.sample),
                "timestamp": self.timestamp,
                "points": [asdict(p) for p in self.points],
                "instrument_id": self.instrument_id,
                "zero_offset_counts": self.zero_offset_counts,
                "calibration_check": self.calibration_check,
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, text: str) -> "Run":
        d = json.loads(text)
        method = TestMethod.from_dict(d["method"])
        sample = Sample(**d["sample"])
        points = [DataPoint(**p) for p in d["points"]]
        return cls(
            method=method,
            sample=sample,
            timestamp=d["timestamp"],
            points=points,
            instrument_id=d.get("instrument_id", ""),
            zero_offset_counts=d.get("zero_offset_counts"),
            calibration_check=d.get("calibration_check"),
        )
