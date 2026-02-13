from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from generators.workout_generator import WorkoutGenerator


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", required=True, dest="workout_type")
    parser.add_argument("--duration", required=True, type=int)
    parser.add_argument("--ftp", type=int, default=None)
    parser.add_argument("--level", default="intermediate")

    args = parser.parse_args()

    generator = WorkoutGenerator()
    workout = generator.generate(
        duration=args.duration,
        workout_type=args.workout_type,
        user_ftp=args.ftp,
        fitness_level=args.level,
    )

    os.makedirs(os.path.join("data", "generated"), exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    path = os.path.join("data", "generated", f"workout_{timestamp}.json")

    with open(path, "w", encoding="utf-8") as handle:
        json.dump(workout, handle, indent=2)

    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
