from __future__ import annotations

from datetime import datetime
from uuid import uuid4
from typing import Any

from generators.personalizer import personalize
from generators.scaler import (
    scale_cadence,
    scale_hiit,
    scale_power,
    scale_sweetspot,
    scale_vo2max,
    scale_zone2,
)
from generators.template_manager import get_template
from generators.validator import validate_generated


class WorkoutGenerator:
    def __init__(self, template_path: str | None = None) -> None:
        self._template_path = template_path
        self._scalers = {
            "HIIT": scale_hiit,
            "Zone 2": scale_zone2,
            "Sweet Spot": scale_sweetspot,
            "VO2max": scale_vo2max,
            "Power": scale_power,
            "Cadence": scale_cadence,
        }

    def generate(
        self,
        duration: int,
        workout_type: str,
        user_ftp: int | None = None,
        fitness_level: str = "intermediate",
        strict: bool = False,
    ) -> dict[str, Any]:
        template = get_template(workout_type, duration, path=self._template_path or "data/templates/workout_templates.json")
        if not template:
            raise ValueError(f"No template for {workout_type}")

        return self.generate_from_template(
            template=template,
            duration=duration,
            workout_type=workout_type,
            user_ftp=user_ftp,
            fitness_level=fitness_level,
            template_id=None,
            strict=strict,
        )

    def generate_from_template(
        self,
        template: dict[str, Any],
        duration: int,
        workout_type: str,
        user_ftp: int | None = None,
        fitness_level: str = "intermediate",
        template_id: int | None = None,
        strict: bool = True,
    ) -> dict[str, Any]:
        scaler = self._scalers.get(workout_type)
        if not scaler:
            raise ValueError(f"No scaler for {workout_type}")

        scaled = scaler(template, duration, workout_type)
        intervals = personalize(scaled["intervals"], user_ftp, fitness_level)
        for interval in intervals:
            if "power_watts" not in interval:
                interval["power_watts"] = None
            if "intensity_level" not in interval:
                interval["intensity_level"] = _parse_intensity(interval.get("power_level", ""))

        actual_seconds = sum(int(item.get("duration_seconds", 0)) for item in intervals)
        generated_id = f"generated-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        workout = {
            "workout_id": str(uuid4()),
            "template_id": template_id,
            "video_id": generated_id,
            "title": f"Generated {workout_type} {duration}min",
            "url": "",
            "workout_type": workout_type,
            "duration_minutes": duration,
            "target_duration_seconds": duration * 60,
            "actual_duration_seconds": actual_seconds,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "intervals": intervals,
        }

        validation = validate_generated(workout, duration, workout_type)
        workout["validation"] = validation
        if strict and not validation["ok"]:
            reason = ", ".join(validation.get("reasons", [])[:3]) or "validation failed"
            raise ValueError(f"Workout generation failed validation: {reason}")
        return workout


def _parse_intensity(value: str) -> float | None:
    if not value:
        return None
    token = value.split("/")[0].strip() if "/" in value else value.strip()
    try:
        return float(token)
    except ValueError:
        return None
