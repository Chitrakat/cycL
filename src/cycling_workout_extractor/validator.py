from __future__ import annotations

from typing import Any


def is_probable_workout(
    title: str, description: str, non_workout_keywords: list[str]
) -> bool:
    haystack = f"{title} {description}".lower()
    return not any(keyword.lower() in haystack for keyword in non_workout_keywords)


def validate_workout(record: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    required_fields = ["video_id", "title", "url", "workout_type", "duration_minutes"]

    for field in required_fields:
        if not record.get(field):
            reasons.append(f"missing {field}")

    intervals = record.get("intervals", [])
    if not intervals:
        reasons.append("missing intervals")
    else:
        for idx, interval in enumerate(intervals, start=1):
            if not interval.get("start_time") or not interval.get("end_time"):
                reasons.append(f"interval {idx} missing time bounds")
                break

    return len(reasons) == 0, reasons
