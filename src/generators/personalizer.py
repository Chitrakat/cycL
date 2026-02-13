from __future__ import annotations

from typing import Any

FITNESS_ADJUSTMENTS = {
    "beginner": {"power": 0.9, "rest": 1.2},
    "intermediate": {"power": 1.0, "rest": 1.0},
    "advanced": {"power": 1.05, "rest": 0.85},
}


def personalize(
    intervals: list[dict[str, Any]], user_ftp: int | None, fitness_level: str
) -> list[dict[str, Any]]:
    adjustments = FITNESS_ADJUSTMENTS.get(fitness_level, FITNESS_ADJUSTMENTS["intermediate"])

    for interval in intervals:
        power_level = interval.get("power_level", "")
        if user_ftp and power_level and "/" in power_level:
            power = int(power_level.split("/")[0])
            watts = int(round((power / 10) * user_ftp * adjustments["power"]))
            interval["power_watts"] = watts
        elif user_ftp:
            interval["power_watts"] = int(round(user_ftp * 0.6 * adjustments["power"]))

        if interval.get("zone") == "recovery":
            duration = int(interval.get("duration_seconds", 0))
            interval["duration_seconds"] = int(round(duration * adjustments["rest"]))

    return intervals
