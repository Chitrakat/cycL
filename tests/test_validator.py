from __future__ import annotations

from generators.validator import validate_generated


def test_validate_generated_duration():
    workout = {
        "intervals": [
            {"duration_seconds": 600, "zone": "main set", "cadence_rpm": 90}
        ]
    }
    ok, reasons = validate_generated(workout, target_duration=10)
    assert ok
    assert reasons == []
