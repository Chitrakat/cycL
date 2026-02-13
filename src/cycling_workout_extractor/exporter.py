from __future__ import annotations

import json
import os
from typing import Any

import pandas as pd


def ensure_output_dirs(output_config: dict[str, str]) -> None:
    os.makedirs(output_config["workouts_dir"], exist_ok=True)
    os.makedirs(output_config["logs_dir"], exist_ok=True)


def write_json(record: dict[str, Any], workouts_dir: str) -> None:
    os.makedirs(workouts_dir, exist_ok=True)
    filename = f"{record['video_id']}.json"
    path = os.path.join(workouts_dir, filename)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2)


def write_summary_csv(rows: list[dict[str, Any]], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if rows:
        df = pd.DataFrame(rows)
    else:
        df = pd.DataFrame(
            columns=[
                "video_id",
                "title",
                "url",
                "workout_type",
                "duration_minutes",
                "intervals_count",
                "status",
                "review_reason",
            ]
        )
    df.to_csv(path, index=False)


def write_review_log(entries: list[str], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(f"{entry}\n")
