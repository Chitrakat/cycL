from __future__ import annotations

from typing import Any


def validate_generated(
    workout: dict[str, Any], target_duration: int
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    intervals = workout.get("intervals", [])

    if not intervals:
        reasons.append("missing intervals")
        return False, reasons

    total_seconds = sum(interval.get("duration_seconds", 0) for interval in intervals)
    total_minutes = int(round(total_seconds / 60))
    if abs(total_minutes - target_duration) > 2:
        reasons.append("duration mismatch")

    for interval in intervals:
        power_watts = interval.get("power_watts")
        cadence = interval.get("cadence_rpm", 0)
        if power_watts is not None and power_watts < 30:
            reasons.append("unrealistic power")
            break
        if cadence and (cadence < 50 or cadence > 140):
            reasons.append("unrealistic cadence")
            break

    recovery_seconds = sum(
        interval.get("duration_seconds", 0)
        for interval in intervals
        if interval.get("zone") == "recovery"
    )
    if recovery_seconds and recovery_seconds < 60:
        reasons.append("insufficient recovery")

    return len(reasons) == 0, reasons
