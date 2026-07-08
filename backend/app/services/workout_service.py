"""Workout generation and management service."""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import GeneratedWorkout, WorkoutTemplate
from app.db.schemas import GeneratedWorkoutResponse

# Add /src to Python path for importing generators
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from generators.workout_generator import WorkoutGenerator

logger = logging.getLogger(__name__)


INTERVAL_COUNT_BOUNDS: dict[str, tuple[int, int]] = {
    "HIIT": (6, 14),
    "Zone 2": (1, 1),
    "Sweet Spot": (2, 4),
    "VO2max": (4, 8),
    "Power": (3, 6),
    "Cadence": (6, 12),
}

REQUIRED_SCALING_FIELDS = {
    "interval_count",
    "work_duration_seconds",
    "rest_duration_seconds",
    "warmup_minutes",
    "cooldown_minutes",
    "default_power_level",
    "default_cadence_rpm",
}


class WorkoutService:
    """Service for generating and managing personalized workouts."""

    def __init__(self, db: Session) -> None:
        """Initialize the workout service.

        Args:
            db: SQLAlchemy session for database operations
        """
        self.db = db
        template_path = str(project_root / "data" / "templates" / "workout_templates.json")
        self.generator = WorkoutGenerator(template_path=template_path)

    def generate_workout(
        self,
        user_ftp: int,
        workout_type: str | None = None,
        duration_minutes: int | None = None,
        fitness_level: str = "intermediate",
        user_id: str | None = None,
        scaling_type: str | None = None,
        template_id: int | None = None,
    ) -> dict[str, Any]:
        """Generate a personalized workout from a template.

        Args:
            workout_type: Type of workout (e.g., "HIIT", "Zone 2")
            duration_minutes: Duration in minutes
            user_ftp: User's functional threshold power in watts
            fitness_level: Fitness level ("beginner", "intermediate", "advanced")
            user_id: Optional user identifier
            scaling_type: Optional scaling type for the workout
            template_id: Template identifier (preferred source of truth)

        Returns:
            Dictionary with generated workout data including:
            - workout_id: Database ID of the generated workout
            - workout_type: Type of workout
            - duration_minutes: Duration in minutes
            - power_profile: List of power levels
            - segments: Detailed workout segments
            - ftp: User's FTP used for generation

        Raises:
            ValueError: If template not found or generation fails
        """
        logger.info(
            f"Generating workout request type={workout_type} duration={duration_minutes} "
            f"(FTP: {user_ftp}W, Level: {fitness_level})"
        )

        # Get template from database, preferring an explicit template_id.
        if template_id is not None:
            template = self.db.query(WorkoutTemplate).filter(
                WorkoutTemplate.id == template_id
            ).first()
        else:
            if workout_type is None or duration_minutes is None:
                raise ValueError("workout_type and duration_minutes are required when template_id is not provided")
            template = self.db.query(WorkoutTemplate).filter(
                WorkoutTemplate.workout_type == workout_type,
                WorkoutTemplate.duration_minutes == duration_minutes,
            ).first()

        if not template:
            logger.warning(
                f"Template not found: template_id={template_id}, type={workout_type}, duration={duration_minutes}"
            )
            raise ValueError("No matching template found")

        logger.debug(f"Found template: {template.name} (ID: {template.id})")

        try:
            resolved_workout_type = template.workout_type
            resolved_duration = template.duration_minutes
            generator_template = self._to_generator_template(template)

            # Generate workout using the selected DB template directly.
            generated_data = self.generator.generate_from_template(
                template=generator_template,
                duration=resolved_duration,
                workout_type=resolved_workout_type,
                user_ftp=user_ftp,
                fitness_level=fitness_level,
                template_id=template.id,
                strict=True,
            )

            logger.info(f"Workout generated successfully")

            # Extract power profile from intervals if available
            power_profile = []
            if "intervals" in generated_data:
                for interval in generated_data["intervals"]:
                    intensity = interval.get("intensity_level")
                    if isinstance(intensity, (int, float)):
                        power_profile.append(float(intensity) / 10.0)
                    else:
                        power_level = interval.get("power_level", 0)
                        if isinstance(power_level, str) and "/" in power_level:
                            parts = power_level.split("/")
                            power_profile.append(float(parts[0]) / float(parts[1]))
                        elif isinstance(power_level, str):
                            try:
                                power_profile.append(float(power_level))
                            except (ValueError, TypeError):
                                power_profile.append(0.0)
                        else:
                            power_profile.append(float(power_level) if power_level else 0.0)

            # Extract segments (intervals with metadata)
            segments = generated_data.get("intervals", [])

            # Save to database
            db_workout = GeneratedWorkout(
                user_id=user_id,
                template_id=template.id,
                workout_type=resolved_workout_type,
                duration_minutes=resolved_duration,
                ftp=user_ftp,
                fitness_level=fitness_level,
                scaling_type=scaling_type,
                power_profile=power_profile,
                segments=segments,
                workout_metadata={
                    "validation": generated_data.get("validation"),
                    "title": generated_data.get("title"),
                    "template_id": template.id,
                    "target_duration_seconds": generated_data.get("target_duration_seconds"),
                    "actual_duration_seconds": generated_data.get("actual_duration_seconds"),
                },
                created_at=datetime.utcnow(),
                generated_at=datetime.utcnow(),
            )

            self.db.add(db_workout)
            self.db.commit()
            self.db.refresh(db_workout)

            logger.info(
                f"Workout saved to database (ID: {db_workout.id})"
            )

            # Return the database object response
            return GeneratedWorkoutResponse.model_validate(db_workout).model_dump()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Workout generation failed: {str(e)}", exc_info=True)
            raise

    def get_templates(
        self,
        workout_type: str | None = None,
        duration_minutes: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get templates for frontend discovery and selection."""
        query = self.db.query(WorkoutTemplate)
        if workout_type:
            query = query.filter(WorkoutTemplate.workout_type == workout_type)
        if duration_minutes is not None:
            query = query.filter(WorkoutTemplate.duration_minutes == duration_minutes)

        templates = query.order_by(
            WorkoutTemplate.workout_type.asc(),
            WorkoutTemplate.duration_minutes.asc(),
            WorkoutTemplate.id.asc(),
        ).limit(limit).all()

        return [
            {
                "id": item.id,
                "workout_type": item.workout_type,
                "duration_minutes": item.duration_minutes,
                "name": item.name,
            }
            for item in templates
        ]

    def get_template_quality_report(
        self,
        workout_type: str | None = None,
        limit: int = 200,
        include_templates: bool = True,
    ) -> dict[str, Any]:
        """Build a quality report for template scaling configuration and constraints."""
        query = self.db.query(WorkoutTemplate)
        if workout_type:
            query = query.filter(WorkoutTemplate.workout_type == workout_type)

        rows = query.order_by(
            WorkoutTemplate.workout_type.asc(),
            WorkoutTemplate.duration_minutes.asc(),
            WorkoutTemplate.id.asc(),
        ).limit(limit).all()

        by_type: dict[str, dict[str, int]] = {}
        evaluated: list[dict[str, Any]] = []

        missing_scaling_factors = 0
        failing_bounds = 0
        failing_required_fields = 0
        failing_duration_fit = 0

        for item in rows:
            type_stats = by_type.setdefault(
                item.workout_type,
                {
                    "total": 0,
                    "missing_scaling_factors": 0,
                    "bounds_failures": 0,
                    "required_field_failures": 0,
                    "duration_fit_failures": 0,
                },
            )
            type_stats["total"] += 1

            issues: list[str] = []
            scaling = item.scaling_factors if isinstance(item.scaling_factors, dict) else {}

            if not scaling:
                issues.append("missing scaling_factors")
                missing_scaling_factors += 1
                type_stats["missing_scaling_factors"] += 1

            missing_fields = sorted(REQUIRED_SCALING_FIELDS - set(scaling.keys()))
            if missing_fields:
                issues.append(f"missing required scaling fields: {', '.join(missing_fields)}")
                failing_required_fields += 1
                type_stats["required_field_failures"] += 1

            interval_count = _safe_int(scaling.get("interval_count"), default=0)
            lower, upper = INTERVAL_COUNT_BOUNDS.get(item.workout_type, (1, max(1, interval_count)))
            if interval_count <= 0 or interval_count < lower or interval_count > upper:
                issues.append(
                    f"interval_count {interval_count} outside bounds {lower}-{upper}"
                )
                failing_bounds += 1
                type_stats["bounds_failures"] += 1

            warmup_minutes = _safe_int(scaling.get("warmup_minutes"), default=5)
            cooldown_minutes = _safe_int(scaling.get("cooldown_minutes"), default=5)
            work_seconds = _safe_int(scaling.get("work_duration_seconds"), default=60)
            rest_seconds = _safe_int(scaling.get("rest_duration_seconds"), default=60)

            expected_seconds = (
                (warmup_minutes + cooldown_minutes) * 60
                + max(0, interval_count) * max(1, work_seconds + rest_seconds)
            )
            target_seconds = item.duration_minutes * 60
            duration_delta = expected_seconds - target_seconds
            if abs(duration_delta) > 300:
                issues.append(
                    f"estimated duration delta too high: {duration_delta}s"
                )
                failing_duration_fit += 1
                type_stats["duration_fit_failures"] += 1

            status = "ok" if not issues else "needs_attention"
            evaluated.append(
                {
                    "id": item.id,
                    "workout_type": item.workout_type,
                    "duration_minutes": item.duration_minutes,
                    "name": item.name,
                    "status": status,
                    "issues": issues,
                    "duration_delta_seconds": duration_delta,
                }
            )

        report: dict[str, Any] = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "summary": {
                "total_templates": len(rows),
                "missing_scaling_factors": missing_scaling_factors,
                "failing_bounds": failing_bounds,
                "failing_required_fields": failing_required_fields,
                "failing_duration_fit": failing_duration_fit,
            },
            "by_workout_type": by_type,
        }
        if include_templates:
            report["templates"] = evaluated
        return report

    def get_workout_by_id(self, workout_id: int) -> GeneratedWorkoutResponse:
        """Retrieve a generated workout by ID.

        Args:
            workout_id: Database ID of the workout

        Returns:
            GeneratedWorkoutResponse with full workout details

        Raises:
            ValueError: If workout not found
        """
        logger.info(f"Retrieving workout ID: {workout_id}")

        workout = self.db.query(GeneratedWorkout).filter(
            GeneratedWorkout.id == workout_id
        ).first()

        if not workout:
            logger.warning(f"Workout not found: {workout_id}")
            raise ValueError(f"Workout not found: {workout_id}")

        logger.debug(f"Found workout: {workout.workout_type}")
        return GeneratedWorkoutResponse.model_validate(workout)

    def get_available_types(self) -> list[str]:
        """Get list of available workout types from templates.

        Returns:
            Sorted list of unique workout types
        """
        logger.info("Fetching available workout types")

        types = self.db.query(WorkoutTemplate.workout_type).distinct().all()
        type_list = sorted(list(set(t[0] for t in types)))

        logger.debug(f"Available types: {type_list}")
        return type_list

    def get_available_durations(self, workout_type: str) -> list[int]:
        """Get available durations for a specific workout type.

        Args:
            workout_type: Type of workout to query

        Returns:
            Sorted list of available durations in minutes

        Raises:
            ValueError: If workout type not found
        """
        logger.info(f"Fetching available durations for: {workout_type}")

        # Verify workout type exists
        type_exists = self.db.query(WorkoutTemplate).filter(
            WorkoutTemplate.workout_type == workout_type
        ).first()

        if not type_exists:
            logger.warning(f"Workout type not found: {workout_type}")
            raise ValueError(f"Workout type not found: {workout_type}")

        # Get all durations for this type
        durations = self.db.query(WorkoutTemplate.duration_minutes).filter(
            WorkoutTemplate.workout_type == workout_type
        ).all()

        duration_list = sorted(list(set(d[0] for d in durations)))

        logger.debug(f"Available durations for {workout_type}: {duration_list}")
        return duration_list

    def get_user_workouts(
        self, user_id: str, limit: int = 10, offset: int = 0
    ) -> dict[str, Any]:
        """Get all workouts for a specific user.

        Args:
            user_id: User identifier
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Dictionary with total count and list of workouts
        """
        logger.info(
            f"Fetching workouts for user: {user_id} (limit={limit}, offset={offset})"
        )

        query = self.db.query(GeneratedWorkout).filter(
            GeneratedWorkout.user_id == user_id
        )

        total = query.count()
        workouts = query.limit(limit).offset(offset).all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "workouts": [
                GeneratedWorkoutResponse.model_validate(w) for w in workouts
            ],
        }

    def _to_generator_template(self, template: WorkoutTemplate) -> dict[str, Any]:
        """Convert DB template row into generator template format."""
        profile = template.power_profile if isinstance(template.power_profile, list) else []
        power_by_zone = template.power_by_zone if isinstance(template.power_by_zone, dict) else {}
        scaling = template.scaling_factors if isinstance(template.scaling_factors, dict) else {}

        return {
            "workout_type": template.workout_type,
            "duration_minutes": template.duration_minutes,
            "interval_count": int(scaling.get("interval_count", max(1, len(profile) // 2) or 1)),
            "work_duration_seconds": int(scaling.get("work_duration_seconds", 60)),
            "rest_duration_seconds": int(scaling.get("rest_duration_seconds", 60)),
            "warmup_minutes": int(scaling.get("warmup_minutes", 5)),
            "cooldown_minutes": int(scaling.get("cooldown_minutes", 5)),
            "default_power_level": str(scaling.get("default_power_level", "5/10")),
            "default_cadence_rpm": int(scaling.get("default_cadence_rpm", 85)),
            "power_profile": profile,
            "power_by_zone": power_by_zone,
        }


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
