from __future__ import annotations

import json

from generators.pattern_analyzer import _build_template, analyze_patterns


def _record(video_id: str, intervals: list[dict[str, object]]) -> dict[str, object]:
    return {
        "video_id": video_id,
        "workout_type": "HIIT",
        "duration_minutes": 30,
        "intervals": intervals,
    }


def test_interval_count_uses_per_workout_median_and_bounds():
    records = [
        _record(
            "a",
            [
                {"duration_seconds": 60, "zone": "main set", "power_level": "8/10", "cadence_rpm": 90},
                {"duration_seconds": 60, "zone": "recovery", "power_level": "2/10", "cadence_rpm": 85},
            ]
            * 40,
        ),
        _record(
            "b",
            [
                {"duration_seconds": 60, "zone": "main set", "power_level": "8/10", "cadence_rpm": 90},
                {"duration_seconds": 60, "zone": "recovery", "power_level": "2/10", "cadence_rpm": 85},
            ]
            * 38,
        ),
    ]

    review_entries: list[dict[str, object]] = []
    template = _build_template(records, "HIIT", 30, review_entries)

    assert 6 <= template["interval_count"] <= 14


def test_unresolvable_missing_zone_goes_to_review():
    records = [
        _record(
            "x",
            [
                {"duration_seconds": 60, "zone": "", "power_level": "", "cadence_rpm": 0},
                {"duration_seconds": 60, "zone": "main set", "power_level": "7/10", "cadence_rpm": 90},
            ],
        )
    ]

    review_entries: list[dict[str, object]] = []
    _ = _build_template(records, "HIIT", 30, review_entries)

    assert review_entries
    assert review_entries[0]["video_id"] == "x"


def test_analyze_patterns_only_uses_standard_durations(tmp_path):
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()

    samples = [
        _record(
            "d25",
            [
                {"duration_seconds": 60, "zone": "main set", "power_level": "7/10", "cadence_rpm": 90},
                {"duration_seconds": 60, "zone": "recovery", "power_level": "2/10", "cadence_rpm": 85},
            ],
        ),
        _record(
            "d35",
            [
                {"duration_seconds": 60, "zone": "main set", "power_level": "7/10", "cadence_rpm": 90},
                {"duration_seconds": 60, "zone": "recovery", "power_level": "2/10", "cadence_rpm": 85},
            ],
        ),
    ]
    samples[0]["duration_minutes"] = 25
    samples[1]["duration_minutes"] = 35

    for item in samples:
        path = processed_dir / f"{item['video_id']}.json"
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(item, handle)

    payload = analyze_patterns(processed_glob=str(processed_dir / "*.json"))
    durations = set(payload["templates"]["HIIT"].keys())
    assert durations.issubset({"20", "30", "40", "60"})
