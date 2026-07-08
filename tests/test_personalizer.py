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


def test_warmup_intensity_is_clamped_for_all_fitness_levels():
    levels = ["beginner", "intermediate", "advanced"]
    for level in levels:
        intervals = [
            {
                "duration_seconds": 300,
                "power_level": "7/10",
                "intensity_level": 7.0,
                "cadence_rpm": 85,
                "zone": "warmup",
            }
        ]
        result = personalize(intervals, user_ftp=250, fitness_level=level)
        assert 1.0 <= float(result[0]["intensity_level"]) <= 4.0
        assert result[0]["power_level"] in {"1/10", "2/10", "3/10", "4/10"}


def test_warmup_watts_not_scaled_by_difficulty():
    base_interval = {
        "duration_seconds": 300,
        "power_level": "4/10",
        "intensity_level": 4.0,
        "cadence_rpm": 85,
        "zone": "warmup",
    }

    beginner = personalize([dict(base_interval)], user_ftp=250, fitness_level="beginner")[0]
    advanced = personalize([dict(base_interval)], user_ftp=250, fitness_level="advanced")[0]
    assert beginner["power_watts"] == advanced["power_watts"]
