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
        zone = str(interval.get("zone", "")).lower()
        is_warmup = zone == "warmup"
        power_adjustment = 1.0 if is_warmup else adjustments["power"]

        power_level = interval.get("power_level", "")
        if user_ftp and power_level and "/" in power_level:
            power = int(power_level.split("/")[0])
            watts = int(round((power / 10) * user_ftp * power_adjustment))
            interval["power_watts"] = watts
        elif user_ftp:
            interval["power_watts"] = int(round(user_ftp * 0.6 * power_adjustment))

        if is_warmup:
            intensity = interval.get("intensity_level")
            if not isinstance(intensity, (int, float)):
                if isinstance(power_level, str) and power_level:
                    token = power_level.split("/")[0].strip() if "/" in power_level else power_level.strip()
                    try:
                        intensity = float(token)
                    except ValueError:
                        intensity = 2.0
                else:
                    intensity = 2.0
            clamped = max(1.0, min(4.0, float(intensity)))
            interval["intensity_level"] = clamped
            interval["power_level"] = f"{int(round(clamped))}/10"

        if zone == "recovery":
            duration = int(interval.get("duration_seconds", 0))
            interval["duration_seconds"] = int(round(duration * adjustments["rest"]))

    return intervals
