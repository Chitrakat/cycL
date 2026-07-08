from __future__ import annotations

from generators.validator import validate_generated


def test_validate_generated_duration():
    workout = {
        "intervals": [
            {"duration_seconds": 600, "zone": "main set", "cadence_rpm": 90}
        ]
    }
    result = validate_generated(workout, target_duration=10, workout_type="Zone 2")
    assert result["ok"]
    assert result["duration_delta_seconds"] == 0
    assert result["reasons"] == []


def test_validate_generated_recovery_intensity_failure():
    workout = {
        "intervals": [
            {"duration_seconds": 120, "zone": "main set", "cadence_rpm": 90, "power_level": "9/10"},
            {"duration_seconds": 120, "zone": "recovery", "cadence_rpm": 85, "power_level": "6/10"},
        ]
    }
    result = validate_generated(workout, target_duration=4, workout_type="HIIT")
    assert not result["ok"]
    assert "recovery intensity too high" in result["failures"]


def test_validate_generated_duration_strict_fail():
    workout = {
        "intervals": [
            {"duration_seconds": 600, "zone": "main set", "cadence_rpm": 90}
        ]
    }
    result = validate_generated(workout, target_duration=8, workout_type="Zone 2")
    assert not result["ok"]
    assert "duration mismatch" in result["failures"]
