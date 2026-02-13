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
    result = scale_hiit(template, 45)
    assert len(result["intervals"]) >= 16


def test_scale_zone2_structure():
    template = {
        "duration_minutes": 30,
        "warmup_minutes": 5,
        "cooldown_minutes": 5,
        "default_power_level": "4/10",
        "default_cadence_rpm": 85,
    }
    result = scale_zone2(template, 40)
    zones = [interval["zone"] for interval in result["intervals"]]
    assert zones == ["warmup", "main set", "cooldown"]
