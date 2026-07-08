from __future__ import annotations

import json
import os
from typing import Any

from generators.pattern_analyzer import (
    DEFAULT_TEMPLATES_PATH,
    STANDARD_DURATIONS,
    TEMPLATE_VERSION,
    analyze_patterns,
    mirror_workouts_to_processed,
    save_templates,
)


def load_templates(path: str = DEFAULT_TEMPLATES_PATH) -> dict[str, Any]:
    regenerate = True
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        version = payload.get("metadata", {}).get("template_version")
        regenerate = version != TEMPLATE_VERSION

    if regenerate:
        mirror_workouts_to_processed()
        payload = analyze_patterns()
        save_templates(payload, path)
        return payload

    return payload


def get_template(
    workout_type: str, duration: int, path: str = DEFAULT_TEMPLATES_PATH
) -> dict[str, Any] | None:
    payload = load_templates(path)
    templates = payload.get("templates", {})
    if workout_type not in templates:
        return None

    durations = templates[workout_type]
    mapped_duration = min(STANDARD_DURATIONS, key=lambda value: abs(value - duration))
    if str(mapped_duration) in durations:
        return durations[str(mapped_duration)]

    available = sorted(int(key) for key in durations.keys())
    if not available:
        return None

    closest = min(available, key=lambda value: abs(value - duration))
    return durations[str(closest)]


def get_available_durations(
    workout_type: str, path: str = DEFAULT_TEMPLATES_PATH
) -> list[int]:
    payload = load_templates(path)
    templates = payload.get("templates", {})
    if workout_type not in templates:
        return STANDARD_DURATIONS[:]

    durations = templates[workout_type]
    available = {int(key) for key in durations.keys()}
    missing = [value for value in STANDARD_DURATIONS if value not in available]
    if missing:
        print(
            f"[template_manager] warning: missing standard durations for {workout_type}: {missing}"
        )

    return STANDARD_DURATIONS[:]
