from __future__ import annotations

from typing import Mapping


def classify_workout_type(
    title: str,
    description: str,
    keywords: Mapping[str, list[str]],
    priority: list[str],
) -> str:
    haystack = f"{title} {description}".lower()

    for workout_type in priority:
        for keyword in keywords.get(workout_type, []):
            if keyword.lower() in haystack:
                return workout_type

    return "Unknown"
