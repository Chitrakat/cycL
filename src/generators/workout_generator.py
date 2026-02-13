from __future__ import annotations

from datetime import datetime
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
    def __init__(self) -> None:
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
    ) -> dict[str, Any]:
        template = get_template(workout_type, duration)
        if not template:
            raise ValueError(f"No template for {workout_type}")

        scaler = self._scalers.get(workout_type)
        if not scaler:
            raise ValueError(f"No scaler for {workout_type}")

        scaled = scaler(template, duration)
        intervals = personalize(scaled["intervals"], user_ftp, fitness_level)

        workout = {
            "video_id": f"generated-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "title": f"Generated {workout_type} {duration}min",
            "url": "",
            "workout_type": workout_type,
            "duration_minutes": duration,
            "intervals": intervals,
        }

        valid, reasons = validate_generated(workout, duration)
        workout["validation"] = {"ok": valid, "reasons": reasons}
        return workout
