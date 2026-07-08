"""Backfill missing template scaling_factors.

Usage:
    python -m app.scripts.backfill_scaling_factors
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import WorkoutTemplate

INTERVAL_BOUNDS: dict[str, tuple[int, int]] = {
    "HIIT": (6, 14),
    "Zone 2": (1, 1),
    "Sweet Spot": (2, 4),
    "VO2max": (4, 8),
    "Power": (3, 6),
    "Cadence": (6, 12),
}


def _clamp_count(workout_type: str, count: int) -> int:
    low, high = INTERVAL_BOUNDS.get(workout_type, (1, max(1, count)))
    return max(low, min(high, count))


def _default_work_rest(template: WorkoutTemplate) -> tuple[int, int]:
    workout_type = template.workout_type
    if workout_type == "HIIT":
        return 90, 100
    if workout_type == "VO2max":
        return 240, 240
    if workout_type in {"Sweet Spot", "Power"}:
        return 600, 240
    if workout_type == "Cadence":
        return 120, 120
    if workout_type == "Zone 2":
        return max(60, (template.duration_minutes - 10) * 60), 60
    return 120, 120


def _estimate_interval_count(template: WorkoutTemplate, work: int, rest: int) -> int:
    workout_type = template.workout_type
    if workout_type == "Zone 2":
        return 1

    if isinstance(template.power_profile, list) and template.power_profile:
        if workout_type in {"HIIT", "VO2max", "Sweet Spot", "Power", "Cadence"}:
            guessed = max(1, len(template.power_profile) // 2)
            return _clamp_count(workout_type, guessed)

    available_main_seconds = max(60, (template.duration_minutes - 10) * 60)
    cycle_seconds = max(1, work + rest)
    guessed = max(1, round(available_main_seconds / cycle_seconds))
    return _clamp_count(workout_type, guessed)


def _build_scaling_factors(template: WorkoutTemplate) -> dict[str, object]:
    work, rest = _default_work_rest(template)
    interval_count = _estimate_interval_count(template, work, rest)

    default_power = "5/10"
    if isinstance(template.power_profile, list) and template.power_profile:
        first = template.power_profile[0]
        if isinstance(first, str) and first:
            default_power = first

    default_cadence = 85
    if isinstance(template.power_by_zone, dict):
        # No cadence in DB template, keep stable default.
        default_cadence = 85

    return {
        "interval_count": interval_count,
        "work_duration_seconds": work,
        "rest_duration_seconds": rest,
        "warmup_minutes": 5,
        "cooldown_minutes": 5,
        "default_power_level": default_power,
        "default_cadence_rpm": default_cadence,
        "backfilled_at": datetime.utcnow().isoformat() + "Z",
    }


def backfill_scaling_factors() -> int:
    db: Session = SessionLocal()
    updated = 0

    try:
        templates = db.query(WorkoutTemplate).all()
        for template in templates:
            scaling = template.scaling_factors
            if isinstance(scaling, dict) and scaling:
                continue

            template.scaling_factors = _build_scaling_factors(template)
            template.updated_at = datetime.utcnow()
            updated += 1

        if updated:
            db.commit()
        return updated
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    changed = backfill_scaling_factors()
    print(f"Updated scaling_factors for {changed} templates")
