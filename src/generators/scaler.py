from __future__ import annotations

from typing import Any

from generators.validator import clamp_warmup_intensity


INTERVAL_COUNT_BOUNDS: dict[str, tuple[int, int]] = {
    "HIIT": (6, 14),
    "Zone 2": (1, 1),
    "Sweet Spot": (2, 4),
    "VO2max": (4, 8),
    "Power": (3, 6),
    "Cadence": (6, 12),
}

MAX_RECOVERY_INTENSITY_BY_TYPE: dict[str, float] = {
    "HIIT": 3.0,
    "VO2max": 3.0,
    "Sweet Spot": 4.0,
    "Power": 4.5,
    "Cadence": 3.5,
}


def scale_hiit(
    template: dict[str, Any], target_duration: int, workout_type: str = "HIIT"
) -> dict[str, Any]:
    base_duration = template["duration_minutes"]
    base_count = max(1, int(template.get("interval_count", 1)))
    ratio = target_duration / base_duration if base_duration else 1
    warmup = int(template.get("warmup_minutes", 5))
    cooldown = int(template.get("cooldown_minutes", 5))
    main_target_seconds = max(60, (target_duration - warmup - cooldown) * 60)
    interval_count = _clamp_interval_count(
        workout_type,
        max(1, int(round(base_count * ratio))),
    )
    work = int(template.get("work_duration_seconds", 30))
    rest = int(template.get("rest_duration_seconds", 30))
    work, rest = _fit_cycle_durations(work, rest, interval_count, main_target_seconds)

    intervals = [
        _interval("warmup", warmup * 60, template, index=0, workout_type=workout_type),
    ]
    intervals = _build_intervals(
        interval_count,
        work,
        rest,
        template,
        start_index=1,
        workout_type=workout_type,
        intervals=intervals,
    )
    intervals.append(
        _interval("cooldown", cooldown * 60, template, index=len(intervals), workout_type=workout_type)
    )
    return _with_durations(intervals, target_duration, template, workout_type)


def scale_zone2(
    template: dict[str, Any], target_duration: int, workout_type: str = "Zone 2"
) -> dict[str, Any]:
    warmup = int(template.get("warmup_minutes", 5))
    cooldown = int(template.get("cooldown_minutes", 5))
    main_minutes = max(1, target_duration - warmup - cooldown)

    intervals = [
        _interval("warmup", warmup * 60, template, index=0, workout_type=workout_type),
        _interval("main set", main_minutes * 60, template, index=1, workout_type=workout_type),
        _interval("cooldown", cooldown * 60, template, index=2, workout_type=workout_type),
    ]
    return _with_durations(intervals, target_duration, template, workout_type)


def scale_sweetspot(
    template: dict[str, Any], target_duration: int, workout_type: str = "Sweet Spot"
) -> dict[str, Any]:
    warmup = int(template.get("warmup_minutes", 5))
    cooldown = int(template.get("cooldown_minutes", 5))
    main_minutes = max(1, target_duration - warmup - cooldown)

    work = int(template.get("work_duration_seconds", 600))
    rest = int(template.get("rest_duration_seconds", 240))
    cycle_minutes = (work + rest) / 60
    interval_count = _clamp_interval_count(
        workout_type,
        max(1, int(round(main_minutes / cycle_minutes))),
    )
    work, rest = _fit_cycle_durations(work, rest, interval_count, main_minutes * 60)

    intervals = [_interval("warmup", warmup * 60, template, index=0, workout_type=workout_type)]
    intervals = _build_intervals(
        interval_count,
        work,
        rest,
        template,
        start_index=1,
        workout_type=workout_type,
        intervals=intervals,
    )
    intervals.append(
        _interval("cooldown", cooldown * 60, template, index=len(intervals), workout_type=workout_type)
    )

    return _with_durations(intervals, target_duration, template, workout_type)


def scale_vo2max(
    template: dict[str, Any], target_duration: int, workout_type: str = "VO2max"
) -> dict[str, Any]:
    work = int(template.get("work_duration_seconds", 240))
    rest = int(template.get("rest_duration_seconds", 240))

    warmup = int(template.get("warmup_minutes", 5))
    cooldown = int(template.get("cooldown_minutes", 5))
    main_minutes = max(1, target_duration - warmup - cooldown)
    cycle_minutes = (work + rest) / 60
    interval_count = _clamp_interval_count(
        workout_type,
        max(1, int(round(main_minutes / cycle_minutes))),
    )
    work, rest = _fit_cycle_durations(work, rest, interval_count, main_minutes * 60)

    intervals = [_interval("warmup", warmup * 60, template, index=0, workout_type=workout_type)]
    intervals = _build_intervals(
        interval_count,
        work,
        rest,
        template,
        start_index=1,
        workout_type=workout_type,
        intervals=intervals,
    )
    intervals.append(
        _interval("cooldown", cooldown * 60, template, index=len(intervals), workout_type=workout_type)
    )

    return _with_durations(intervals, target_duration, template, workout_type)


def scale_power(
    template: dict[str, Any], target_duration: int, workout_type: str = "Power"
) -> dict[str, Any]:
    return scale_sweetspot(template, target_duration, workout_type)


def scale_cadence(
    template: dict[str, Any], target_duration: int, workout_type: str = "Cadence"
) -> dict[str, Any]:
    return scale_zone2(template, target_duration, workout_type)


def _build_intervals(
    count: int,
    work_seconds: int,
    rest_seconds: int,
    template: dict[str, Any],
    start_index: int,
    workout_type: str,
    intervals: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if intervals is None:
        intervals = []
    for _ in range(count):
        work_index = start_index + len(intervals)
        intervals.append(
            _interval(
                "main set",
                work_seconds,
                template,
                index=work_index,
                workout_type=workout_type,
            )
        )
        rest_index = start_index + len(intervals)
        intervals.append(
            _interval(
                "recovery",
                rest_seconds,
                template,
                index=rest_index,
                workout_type=workout_type,
            )
        )
    return intervals


def _interval(
    zone: str,
    duration_seconds: int,
    template: dict[str, Any],
    index: int,
    workout_type: str,
) -> dict[str, Any]:
    power_level = _resolve_power(template, zone, index, workout_type)
    return {
        "start_time": "",
        "end_time": "",
        "duration_seconds": duration_seconds,
        "power_level": power_level,
        "intensity_level": _parse_intensity(power_level),
        "cadence_rpm": template.get("default_cadence_rpm", 0),
        "zone": zone,
        "description": zone,
    }


def _resolve_power(
    template: dict[str, Any], zone: str, index: int, workout_type: str
) -> str:
    zone_key = zone.lower()
    zone_power = template.get("power_by_zone", {}).get(zone_key, "")

    if zone_key in {"recovery", "cooldown", "warmup"}:
        base = zone_power or template.get("default_power_level", "")
        return _clamp_intensity_string(base, workout_type)

    if zone_key in {"warmup", "main set", "recovery", "cooldown"}:
        if zone_power:
            return zone_power

    profile = template.get("power_profile", [])
    if zone_key == "main set" and index < len(profile) and profile[index]:
        return profile[index]

    return template.get("default_power_level", "")


def _with_durations(
    intervals: list[dict[str, Any]],
    target_duration: int,
    template: dict[str, Any],
    workout_type: str,
) -> dict[str, Any]:
    _reconcile_durations(intervals, target_duration * 60)
    clamp_warmup_intensity(intervals)
    total_seconds = sum(item["duration_seconds"] for item in intervals)
    return {
        "intervals": intervals,
        "duration_minutes": target_duration,
        "estimated_seconds": total_seconds,
    }


def _reconcile_durations(intervals: list[dict[str, Any]], target_seconds: int) -> None:
    delta = target_seconds - sum(item["duration_seconds"] for item in intervals)
    if abs(delta) <= 5:
        return

    delta = _adjust_zones(intervals, delta, {"cooldown"}, max_fraction=0.20)
    if abs(delta) <= 5:
        return

    delta = _adjust_zones(intervals, delta, {"recovery"}, max_fraction=0.15)
    if abs(delta) <= 5:
        return

    delta = _adjust_final_work(intervals, delta, max_fraction=0.10)
    if abs(delta) > 5:
        raise ValueError("unable to reconcile duration to target")


def _adjust_zones(
    intervals: list[dict[str, Any]],
    delta: int,
    zones: set[str],
    max_fraction: float,
) -> int:
    if delta == 0:
        return 0

    for interval in intervals:
        zone = str(interval.get("zone", "")).lower()
        if zone not in zones:
            continue
        delta = _adjust_interval_duration(interval, delta, max_fraction)
        if delta == 0:
            break
    return delta


def _adjust_final_work(
    intervals: list[dict[str, Any]], delta: int, max_fraction: float
) -> int:
    for interval in reversed(intervals):
        zone = str(interval.get("zone", "")).lower()
        if zone in {"main set", "work"}:
            return _adjust_interval_duration(interval, delta, max_fraction)
    return delta


def _adjust_interval_duration(
    interval: dict[str, Any], delta: int, max_fraction: float
) -> int:
    if delta == 0:
        return 0

    current = int(interval.get("duration_seconds", 0))
    if current <= 0:
        return delta

    max_change = max(1, int(round(current * max_fraction)))
    amount = min(abs(delta), max_change)

    if delta > 0:
        interval["duration_seconds"] = current + amount
        return delta - amount

    min_duration = 1
    reducible = max(0, current - min_duration)
    if reducible == 0:
        return delta
    amount = min(amount, reducible)
    interval["duration_seconds"] = current - amount
    return delta + amount


def _parse_intensity(value: str) -> float | None:
    if not value:
        return None
    if "/" in value:
        lhs = value.split("/")[0].strip()
    else:
        lhs = value.strip()
    try:
        return float(lhs)
    except ValueError:
        return None


def _clamp_intensity_string(value: str, workout_type: str) -> str:
    intensity = _parse_intensity(value)
    if intensity is None:
        intensity = 2.0

    cap = MAX_RECOVERY_INTENSITY_BY_TYPE.get(workout_type, 3.0)
    clamped = min(intensity, cap)
    if abs(clamped - round(clamped)) < 1e-6:
        return f"{int(round(clamped))}/10"
    return f"{clamped:.1f}/10"


def _clamp_interval_count(workout_type: str, count: int) -> int:
    lower, upper = INTERVAL_COUNT_BOUNDS.get(workout_type, (1, max(1, count)))
    return max(lower, min(upper, count))


def _fit_cycle_durations(
    work_seconds: int,
    rest_seconds: int,
    count: int,
    main_target_seconds: int,
) -> tuple[int, int]:
    if count <= 0:
        return max(1, work_seconds), max(1, rest_seconds)

    base_total = max(1, (work_seconds + rest_seconds) * count)
    ratio = max(0.1, main_target_seconds / base_total)

    scaled_work = max(1, int(round(work_seconds * ratio)))
    scaled_rest = max(1, int(round(rest_seconds * ratio)))
    return scaled_work, scaled_rest
