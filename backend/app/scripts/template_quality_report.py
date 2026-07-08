"""Print template quality report.

Usage:
    python -m app.scripts.template_quality_report
    python -m app.scripts.template_quality_report --type HIIT --summary-only
"""

from __future__ import annotations

import argparse
import json

from app.db.database import SessionLocal
from app.services.workout_service import WorkoutService


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", dest="workout_type", default=None)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        service = WorkoutService(db)
        report = service.get_template_quality_report(
            workout_type=args.workout_type,
            limit=args.limit,
            include_templates=not args.summary_only,
        )
        print(json.dumps(report, indent=2))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
