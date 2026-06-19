from rheocalc32.constants import INSTRUMENT_MODELS, Spindle
from rheocalc32.models import DataPoint, Run, Sample, TestMethod, TestStep


def test_run_json_roundtrip():
    method = TestMethod(
        name="M1",
        instrument_model=INSTRUMENT_MODELS[5],
        spindle=Spindle("LV1", "61", smc=6.4, src=0.0),
        steps=[TestStep()],
    )
    sample = Sample(name="S1")
    run = Run(method=method, sample=sample, timestamp="2026-01-01T00:00:00", points=[
        DataPoint(0.0, 10.0, 5.0, 25.0, 2.79, 1.5, 50.0),
    ])
    text = run.to_json()
    loaded = Run.from_json(text)
    assert loaded.method.name == "M1"
    assert loaded.sample.name == "S1"
    assert len(loaded.points) == 1
    assert loaded.points[0].rpm == 10.0
