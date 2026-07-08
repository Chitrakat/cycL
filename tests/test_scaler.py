from __future__ import annotations

from generators.scaler import scale_hiit, scale_zone2


def test_scale_hiit_interval_count():
    template = {
        "duration_minutes": 30,
        "interval_count": 8,
        "work_duration_seconds": 30,
        "rest_duration_seconds": 30,
        "default_power_level": "7/10",
        "default_cadence_rpm": 90,
    }
    result = scale_hiit(template, 45, "HIIT")
    work_count = sum(1 for item in result["intervals"] if item["zone"] == "main set")
    assert 6 <= work_count <= 14
    assert abs(result["estimated_seconds"] - (45 * 60)) <= 5


def test_scale_hiit_recovery_is_capped():
    template = {
        "duration_minutes": 30,
        "interval_count": 8,
        "work_duration_seconds": 60,
        "rest_duration_seconds": 60,
        "default_power_level": "9/10",
        "default_cadence_rpm": 90,
        "power_profile": ["9/10"] * 20,
        "power_by_zone": {},
    }
    result = scale_hiit(template, 30, "HIIT")
    recovery = [item for item in result["intervals"] if item["zone"] == "recovery"]
    assert recovery
    assert all(item["power_level"] in {"3/10", "2/10", "1/10"} for item in recovery)


def test_scale_zone2_structure():
    template = {
        "duration_minutes": 30,
        "warmup_minutes": 5,
        "cooldown_minutes": 5,
        "default_power_level": "4/10",
        "default_cadence_rpm": 85,
    }
    result = scale_zone2(template, 40, "Zone 2")
    zones = [interval["zone"] for interval in result["intervals"]]
    assert zones == ["warmup", "main set", "cooldown"]
    assert abs(result["estimated_seconds"] - (40 * 60)) <= 5
