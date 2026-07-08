"""Rebuild templates using standardized durations (20/30/40/60).

Usage:
    python backend/scripts/rebuild_templates_v2.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from generators.pattern_analyzer import analyze_patterns, save_templates  # noqa: E402

OLD_PATH = ROOT / "data" / "templates" / "workout_templates.json"
NEW_PATH = ROOT / "data" / "templates" / "workout_templates_v2.json"
PROCESSED_GLOB = str(ROOT / "data" / "processed" / "*.json")


def _duration_map(payload: dict) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    templates = payload.get("templates", {}) if isinstance(payload, dict) else {}
    for workout_type, buckets in templates.items():
        if not isinstance(buckets, dict):
            continue
        values = sorted(int(key) for key in buckets.keys())
        result[workout_type] = values
    return result


def main() -> int:
    if not OLD_PATH.exists():
        raise FileNotFoundError(f"Missing template file: {OLD_PATH}")

    with open(OLD_PATH, "r", encoding="utf-8") as handle:
        old_payload = json.load(handle)

    new_payload = analyze_patterns(processed_glob=PROCESSED_GLOB)
    save_templates(new_payload, str(NEW_PATH))

    old_map = _duration_map(old_payload)
    new_map = _duration_map(new_payload)
    workout_types = sorted(set(old_map.keys()) | set(new_map.keys()))

    print(f"Wrote standardized templates: {NEW_PATH}")
    print("Duration diff report:")
    for workout_type in workout_types:
        old_values = old_map.get(workout_type, [])
        new_values = new_map.get(workout_type, [])
        print(f"- {workout_type}: old={old_values} new={new_values}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
