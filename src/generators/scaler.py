from __future__ import annotations

from typing import Any


def scale_hiit(template: dict[str, Any], target_duration: int) -> dict[str, Any]:
    base_duration = template["duration_minutes"]
    base_count = max(1, int(template.get("interval_count", 1)))
    ratio = target_duration / base_duration if base_duration else 1
    interval_count = max(1, int(round(base_count * ratio)))
    work = int(template.get("work_duration_seconds", 30))
    rest = int(template.get("rest_duration_seconds", 30))

    intervals = _build_intervals(interval_count, work, rest, template, start_index=0)
    return _with_durations(intervals, target_duration, template)


def scale_zone2(template: dict[str, Any], target_duration: int) -> dict[str, Any]:
    warmup = int(template.get("warmup_minutes", 5))
    cooldown = int(template.get("cooldown_minutes", 5))
    main_minutes = max(1, target_duration - warmup - cooldown)

    intervals = [
        _interval("warmup", warmup * 60, template, index=0),
        _interval("main set", main_minutes * 60, template, index=1),
        _interval("cooldown", cooldown * 60, template, index=2),
    ]
    return _with_durations(intervals, target_duration, template)


def scale_sweetspot(template: dict[str, Any], target_duration: int) -> dict[str, Any]:
    warmup = int(template.get("warmup_minutes", 5))
    cooldown = int(template.get("cooldown_minutes", 5))
    main_minutes = max(1, target_duration - warmup - cooldown)

    work = int(template.get("work_duration_seconds", 600))
    rest = int(template.get("rest_duration_seconds", 240))
    cycle_minutes = (work + rest) / 60
    interval_count = max(1, int(round(main_minutes / cycle_minutes)))

    intervals = [_interval("warmup", warmup * 60, template, index=0)]
    intervals.extend(
        _build_intervals(interval_count, work, rest, template, start_index=1)
    )
    intervals.append(
        _interval("cooldown", cooldown * 60, template, index=len(intervals))
    )

    return _with_durations(intervals, target_duration, template)


def scale_vo2max(template: dict[str, Any], target_duration: int) -> dict[str, Any]:
    work = int(template.get("work_duration_seconds", 240))
    rest = int(template.get("rest_duration_seconds", 240))

    warmup = int(template.get("warmup_minutes", 5))
    cooldown = int(template.get("cooldown_minutes", 5))
    main_minutes = max(1, target_duration - warmup - cooldown)
    cycle_minutes = (work + rest) / 60
    interval_count = max(1, int(round(main_minutes / cycle_minutes)))

    intervals = [_interval("warmup", warmup * 60, template, index=0)]
    intervals.extend(
        _build_intervals(interval_count, work, rest, template, start_index=1)
    )
    intervals.append(
        _interval("cooldown", cooldown * 60, template, index=len(intervals))
    )

    return _with_durations(intervals, target_duration, template)


def scale_power(template: dict[str, Any], target_duration: int) -> dict[str, Any]:
    return scale_sweetspot(template, target_duration)


def scale_cadence(template: dict[str, Any], target_duration: int) -> dict[str, Any]:
    return scale_zone2(template, target_duration)


def _build_intervals(
    count: int,
    work_seconds: int,
    rest_seconds: int,
    template: dict[str, Any],
    start_index: int,
) -> list[dict[str, Any]]:
    intervals: list[dict[str, Any]] = []
    for _ in range(count):
        work_index = start_index + len(intervals)
        intervals.append(_interval("main set", work_seconds, template, index=work_index))
        rest_index = start_index + len(intervals)
        intervals.append(
            _interval("recovery", rest_seconds, template, index=rest_index)
        )
    return intervals


def _interval(
    zone: str, duration_seconds: int, template: dict[str, Any], index: int
) -> dict[str, Any]:
    return {
        "start_time": "",
        "end_time": "",
        "duration_seconds": duration_seconds,
        "power_level": _resolve_power(template, zone, index),
        "cadence_rpm": template.get("default_cadence_rpm", 0),
        "zone": zone,
        "description": zone,
    }


def _resolve_power(template: dict[str, Any], zone: str, index: int) -> str:
    profile = template.get("power_profile", [])
    if index < len(profile) and profile[index]:
        return profile[index]

    zone_key = zone.lower()
    if zone_key in {"warmup", "main set", "recovery", "cooldown"}:
        zone_power = template.get("power_by_zone", {}).get(zone_key, "")
        if zone_power:
            return zone_power

    return template.get("default_power_level", "")


def _with_durations(
    intervals: list[dict[str, Any]],
    target_duration: int,
    template: dict[str, Any],
) -> dict[str, Any]:
    total_seconds = sum(item["duration_seconds"] for item in intervals)
    return {
        "intervals": intervals,
        "duration_minutes": target_duration,
        "estimated_seconds": total_seconds,
    }
