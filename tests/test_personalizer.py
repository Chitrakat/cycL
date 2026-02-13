from __future__ import annotations

from generators.personalizer import personalize


def test_personalize_beginner_adjustment():
    intervals = [
        {
            "duration_seconds": 60,
            "power_level": "8/10",
            "cadence_rpm": 90,
            "zone": "recovery",
        }
    ]
    result = personalize(intervals, user_ftp=200, fitness_level="beginner")
    assert result[0]["power_watts"] == 144
    assert result[0]["duration_seconds"] == 72
