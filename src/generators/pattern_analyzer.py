from __future__ import annotations

import glob
import json
import os
from collections import defaultdict
from statistics import median
from typing import Any

DEFAULT_TEMPLATES_PATH = os.path.join("data", "templates", "workout_templates.json")
DEFAULT_PROCESSED_GLOB = os.path.join("data", "processed", "*.json")
DEFAULT_REVIEW_PATH = os.path.join("data", "templates", "needs_review.json")
TEMPLATE_VERSION = 3

INTERVAL_COUNT_BOUNDS: dict[str, tuple[int, int]] = {
    "HIIT": (6, 14),
    "Zone 2": (1, 1),
    "Sweet Spot": (2, 4),
    "VO2max": (4, 8),
    "Power": (3, 6),
    "Cadence": (6, 12),
}


def mirror_workouts_to_processed(
    workouts_dir: str = "workouts", processed_dir: str = "data/processed"
) -> int:
    os.makedirs(processed_dir, exist_ok=True)
    count = 0
    for path in glob.glob(os.path.join(workouts_dir, "*.json")):
        filename = os.path.basename(path)
        target = os.path.join(processed_dir, filename)
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        with open(target, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        count += 1
    return count


def analyze_patterns(
    processed_glob: str = DEFAULT_PROCESSED_GLOB,
) -> dict[str, Any]:
    review_entries: list[dict[str, Any]] = []
    grouped: dict[str, dict[int, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for path in glob.glob(processed_glob):
        with open(path, "r", encoding="utf-8") as handle:
            record = json.load(handle)
        workout_type = record.get("workout_type", "Unknown")
        duration = int(record.get("duration_minutes", 0))
        intervals = record.get("intervals", [])
        if duration and intervals:
            grouped[workout_type][duration].append(record)

    templates: dict[str, dict[str, Any]] = {}
    for workout_type, durations in grouped.items():
        templates[workout_type] = {}
        for duration, records in durations.items():
            template = _build_template(records, workout_type, duration, review_entries)
            templates[workout_type][str(duration)] = template

    _save_review_entries(review_entries)

    return {
        "metadata": {
            "source_glob": processed_glob,
            "template_version": TEMPLATE_VERSION,
            "needs_review_count": len(review_entries),
        },
        "templates": templates,
    }


def save_templates(payload: dict[str, Any], path: str = DEFAULT_TEMPLATES_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _build_template(
    records: list[dict[str, Any]],
    workout_type: str,
    duration: int,
    review_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    intervals = _flatten_intervals(records, review_entries)
    work_durations = [item["duration_seconds"] for item in intervals if item["is_work"]]
    rest_durations = [item["duration_seconds"] for item in intervals if not item["is_work"]]

    work_duration = int(median(work_durations)) if work_durations else 0
    rest_duration = int(median(rest_durations)) if rest_durations else 0

    power_profile = _power_profile(records, review_entries)
    power_by_zone = _power_by_zone(records, review_entries)

    per_workout_counts = [
        _per_workout_interval_count(record, workout_type, review_entries)
        for record in records
    ]
    per_workout_counts = [count for count in per_workout_counts if count > 0]
    interval_count = int(round(median(per_workout_counts))) if per_workout_counts else 1
    interval_count = _clamp_interval_count(workout_type, interval_count)

    return {
        "workout_type": workout_type,
        "duration_minutes": duration,
        "interval_count": interval_count,
        "work_duration_seconds": work_duration,
        "rest_duration_seconds": rest_duration,
        "work_rest_ratio": _ratio(work_duration, rest_duration),
        "warmup_minutes": 5,
        "cooldown_minutes": 5,
        "default_power_level": _median_power(records, review_entries),
        "default_cadence_rpm": _median_cadence(records, review_entries),
        "power_profile": power_profile,
        "power_by_zone": power_by_zone,
    }


def _flatten_intervals(
    records: list[dict[str, Any]], review_entries: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for record in records:
        intervals = record.get("intervals", [])
        for idx, interval in enumerate(intervals):
            duration = int(interval.get("duration_seconds", 0))
            zone = _resolve_interval_zone(intervals, idx, review_entries, record)
            if zone == "":
                continue
            is_work = zone not in {"recovery", "cooldown"}
            flattened.append(
                {
                    "duration_seconds": duration,
                    "is_work": is_work,
                }
            )
    return flattened


def _ratio(work_seconds: int, rest_seconds: int) -> str:
    if not work_seconds or not rest_seconds:
        return ""
    return f"{work_seconds}:{rest_seconds}"


def _median_power(
    records: list[dict[str, Any]], review_entries: list[dict[str, Any]]
) -> str:
    values: list[int] = []
    for record in records:
        intervals = record.get("intervals", [])
        for idx, interval in enumerate(intervals):
            zone = _resolve_interval_zone(intervals, idx, review_entries, record)
            if not zone:
                continue
            power = interval.get("power_level", "")
            if power and "/" in power:
                try:
                    values.append(int(power.split("/")[0]))
                except ValueError:
                    continue
    if not values:
        return ""
    return f"{int(median(values))}/10"


def _power_profile(
    records: list[dict[str, Any]], review_entries: list[dict[str, Any]]
) -> list[str]:
    sequences: list[list[int | None]] = []
    max_len = 0
    for record in records:
        intervals = record.get("intervals", [])
        values: list[int | None] = []
        for idx, interval in enumerate(intervals):
            zone = _resolve_interval_zone(intervals, idx, review_entries, record)
            if zone == "":
                values.append(None)
                continue
            value = _parse_power(interval.get("power_level", ""))
            values.append(value)
        max_len = max(max_len, len(values))
        sequences.append(values)

    profile: list[str] = []
    for idx in range(max_len):
        bucket: list[int] = []
        for seq in sequences:
            if idx < len(seq) and seq[idx] is not None:
                bucket.append(int(seq[idx]))
        if bucket:
            profile.append(f"{int(median(bucket))}/10")
        else:
            profile.append("")

    return profile


def _power_by_zone(
    records: list[dict[str, Any]], review_entries: list[dict[str, Any]]
) -> dict[str, str]:
    buckets: dict[str, list[int]] = {"warmup": [], "main set": [], "recovery": [], "cooldown": []}
    for record in records:
        intervals = record.get("intervals", [])
        for idx, interval in enumerate(intervals):
            zone = _resolve_interval_zone(intervals, idx, review_entries, record)
            zone_key = _normalize_zone(zone)
            if not zone_key:
                continue
            power = _parse_power(interval.get("power_level", ""))
            if power is not None:
                buckets[zone_key].append(power)

    return {
        zone: f"{int(median(values))}/10" if values else ""
        for zone, values in buckets.items()
    }


def _parse_power(value: str) -> int | None:
    if not value:
        return None
    if "/" in value:
        token = value.split("/")[0].strip()
    else:
        token = value.strip()
    if not token.isdigit():
        return None
    return int(token)


def _normalize_zone(zone: str) -> str:
    if not zone:
        return ""
    if "warm" in zone:
        return "warmup"
    if "cool" in zone:
        return "cooldown"
    if "recovery" in zone:
        return "recovery"
    if "main" in zone:
        return "main set"
    return ""


def _median_cadence(
    records: list[dict[str, Any]], review_entries: list[dict[str, Any]]
) -> int:
    values: list[int] = []
    for record in records:
        intervals = record.get("intervals", [])
        for idx, interval in enumerate(intervals):
            zone = _resolve_interval_zone(intervals, idx, review_entries, record)
            if not zone:
                continue
            cadence = int(interval.get("cadence_rpm", 0) or 0)
            if cadence > 0:
                values.append(int(cadence))
    return int(median(values)) if values else 0


def _resolve_interval_zone(
    intervals: list[dict[str, Any]],
    idx: int,
    review_entries: list[dict[str, Any]],
    record: dict[str, Any],
) -> str:
    current = intervals[idx]
    zone = _normalize_zone(str(current.get("zone") or "").lower())
    if zone:
        return zone

    current_power = _parse_power(str(current.get("power_level") or ""))
    prev_power = None
    next_power = None
    if idx > 0:
        prev_power = _parse_power(str(intervals[idx - 1].get("power_level") or ""))
    if idx < len(intervals) - 1:
        next_power = _parse_power(str(intervals[idx + 1].get("power_level") or ""))

    inferred = _infer_zone_from_power(idx, len(intervals), current_power, prev_power, next_power)
    if inferred:
        return inferred

    review_entries.append(
        {
            "video_id": record.get("video_id", "unknown"),
            "interval_index": idx,
            "reason": "unable to infer interval zone",
            "power_level": current.get("power_level", ""),
        }
    )
    return ""


def _infer_zone_from_power(
    idx: int,
    total: int,
    current: int | None,
    previous: int | None,
    following: int | None,
) -> str:
    if current is None:
        return ""

    if idx == 0 and current <= 4:
        return "warmup"
    if idx == total - 1 and current <= 4:
        return "cooldown"
    if current <= 3:
        return "recovery"
    if current >= 6:
        return "main set"
    if previous is not None and previous >= 6 and current <= 4:
        return "recovery"
    if following is not None and following >= 6 and current <= 4:
        return "recovery"
    return ""


def _clamp_interval_count(workout_type: str, interval_count: int) -> int:
    lower, upper = INTERVAL_COUNT_BOUNDS.get(workout_type, (1, max(1, interval_count)))
    return max(lower, min(upper, interval_count))


def _per_workout_interval_count(
    record: dict[str, Any], workout_type: str, review_entries: list[dict[str, Any]]
) -> int:
    if workout_type == "Zone 2":
        return 1

    intervals = record.get("intervals", [])
    work_count = 0
    for idx, _ in enumerate(intervals):
        zone = _resolve_interval_zone(intervals, idx, review_entries, record)
        if zone in {"main set", "work"}:
            work_count += 1

    return work_count


def _save_review_entries(entries: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(DEFAULT_REVIEW_PATH), exist_ok=True)
    with open(DEFAULT_REVIEW_PATH, "w", encoding="utf-8") as handle:
        json.dump(entries, handle, indent=2)
