from __future__ import annotations

import json
import os
from typing import Any

from generators.pattern_analyzer import (
    DEFAULT_TEMPLATES_PATH,
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
    if str(duration) in durations:
        return durations[str(duration)]

    available = sorted(int(key) for key in durations.keys())
    if not available:
        return None

    closest = min(available, key=lambda value: abs(value - duration))
    return durations[str(closest)]
