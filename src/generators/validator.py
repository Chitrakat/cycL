from __future__ import annotations

from typing import Any


RECOVERY_INTENSITY_CAPS: dict[str, float] = {
    "HIIT": 3.0,
    "VO2max": 3.0,
    "Sweet Spot": 4.0,
    "Power": 4.5,
    "Cadence": 3.5,
}


def validate_generated(
    workout: dict[str, Any], target_duration: int, workout_type: str
) -> dict[str, Any]:
    warnings: list[str] = []
    failures: list[str] = []
    intervals = workout.get("intervals", [])

    if not intervals:
        failures.append("missing intervals")
        return {
            "ok": False,
            "reasons": failures,
            "warnings": warnings,
            "failures": failures,
            "duration_delta_seconds": target_duration * 60,
            "recovery_intensity_ok": False,
            "cadence_plausible": False,
            "realism_score": 0,
        }

    total_seconds = sum(interval.get("duration_seconds", 0) for interval in intervals)
    target_seconds = target_duration * 60
    duration_delta = total_seconds - target_seconds
    abs_delta = abs(duration_delta)
    if abs_delta > 30:
        failures.append("duration mismatch")
    elif abs_delta > 5:
        warnings.append("duration drift")

    cadence_plausible = True
    for interval in intervals:
        power_watts = interval.get("power_watts")
        cadence = interval.get("cadence_rpm", 0)
        if power_watts is not None and power_watts < 30:
            failures.append("unrealistic power")
            break
        if cadence and (cadence <= 0 or cadence >= 150):
            failures.append("unrealistic cadence")
            cadence_plausible = False
            break
        if cadence and (cadence < 50 or cadence > 140):
            warnings.append("cadence out of range")
            cadence_plausible = False
            break

    work_seconds = 0
    recovery_seconds = 0
    recovery_intensity_ok = True
    recovery_cap = RECOVERY_INTENSITY_CAPS.get(workout_type, 3.0)
    work_intensity: list[float] = []

    for interval in intervals:
        zone = str(interval.get("zone", "")).lower()
        intensity = _intensity(interval)

        if zone == "recovery":
            recovery_seconds += int(interval.get("duration_seconds", 0))
            if intensity is not None and intensity > recovery_cap + 1:
                failures.append("recovery intensity too high")
                recovery_intensity_ok = False
            elif intensity is not None and intensity > recovery_cap:
                warnings.append("recovery intensity near cap")
                recovery_intensity_ok = False
        elif zone in {"main set", "work"}:
            work_seconds += int(interval.get("duration_seconds", 0))
            if intensity is not None:
                work_intensity.append(intensity)

    if workout_type in {"HIIT", "VO2max"} and work_seconds > 0:
        recovery_ratio = recovery_seconds / work_seconds
        if recovery_ratio < 1.0:
            failures.append("insufficient recovery")
        elif recovery_ratio < 1.5:
            warnings.append("recovery ratio low")

    for idx in range(1, len(work_intensity)):
        jump = abs(work_intensity[idx] - work_intensity[idx - 1])
        if jump > 4:
            failures.append("intensity progression jump")
            break

    score = max(0, 100 - (10 * len(warnings)) - (25 * len(failures)))
    reasons = failures if failures else warnings

    return {
        "ok": len(failures) == 0,
        "reasons": reasons,
        "warnings": warnings,
        "failures": failures,
        "duration_delta_seconds": duration_delta,
        "recovery_intensity_ok": recovery_intensity_ok,
        "cadence_plausible": cadence_plausible,
        "realism_score": score,
    }


def _intensity(interval: dict[str, Any]) -> float | None:
    explicit = interval.get("intensity_level")
    if isinstance(explicit, (int, float)):
        return float(explicit)

    power_level = interval.get("power_level")
    if not isinstance(power_level, str):
        return None

    token = power_level.split("/")[0].strip() if "/" in power_level else power_level.strip()
    try:
        return float(token)
    except ValueError:
        return None
