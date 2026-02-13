from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from cycling_workout_extractor.classifier import classify_workout_type
from cycling_workout_extractor.config import load_config, setup_logging
from cycling_workout_extractor.exporter import (
    ensure_output_dirs,
    write_json,
    write_review_log,
    write_summary_csv,
)
from cycling_workout_extractor.extractor import (
    build_youtube_client,
    fetch_playlist_video_ids,
    fetch_video_metadata,
)
from cycling_workout_extractor.parser import (
    parse_description_timestamps,
    parse_transcript_intervals,
)
from cycling_workout_extractor.validator import is_probable_workout, validate_workout


def main() -> int:
    config_path = os.getenv("CONFIG_PATH", "config.yaml")
    config = load_config(config_path)
    logger = setup_logging(config["output"]["processing_log"])

    ensure_output_dirs(config["output"])

    api_key_env = config["api"].get("key_env", "YOUTUBE_API_KEY")
    api_key = os.getenv(api_key_env)
    if not api_key:
        logger.error("Missing API key in env var: %s", api_key_env)
        return 1

    youtube = build_youtube_client(api_key)

    video_ids: list[str] = []
    for playlist in config["playlists"]:
        playlist_id = playlist["id"]
        logger.info("Fetching playlist: %s", playlist_id)
        video_ids.extend(fetch_playlist_video_ids(youtube, playlist_id))

    unique_ids = sorted(set(video_ids))
    logger.info("Found %d unique videos", len(unique_ids))

    summary_rows = []
    review_entries = []

    for video_id in unique_ids:
        try:
            metadata = fetch_video_metadata(youtube, video_id)
            if not metadata:
                review_entries.append(f"{video_id}\tmissing metadata")
                continue

            title = metadata["title"]
            description = metadata["description"]

            if not is_probable_workout(
                title,
                description,
                config.get("non_workout_keywords", []),
            ):
                review_entries.append(f"{video_id}\tnon-workout: {title}")
                summary_rows.append(
                    {
                        "video_id": video_id,
                        "title": title,
                        "url": metadata["url"],
                        "workout_type": "Non-workout",
                        "duration_minutes": metadata["duration_minutes"],
                        "intervals_count": 0,
                        "status": "skipped",
                        "review_reason": "non-workout",
                    }
                )
                continue

            intervals = parse_description_timestamps(
                description, metadata["duration_seconds"]
            )
            if not intervals:
                intervals = parse_transcript_intervals(
                    video_id, metadata["duration_seconds"]
                )

            workout_type = classify_workout_type(
                title,
                description,
                config["classification"]["keywords"],
                config["classification"]["priority"],
            )

            record = {
                "video_id": video_id,
                "title": title,
                "url": metadata["url"],
                "workout_type": workout_type,
                "duration_minutes": metadata["duration_minutes"],
                "intervals": intervals,
            }

            is_valid, reasons = validate_workout(record)
            status = "ok" if is_valid else "needs_review"
            review_reason = "; ".join(reasons) if reasons else ""
            if not is_valid:
                review_entries.append(f"{video_id}\t{review_reason}")

            if intervals:
                write_json(record, config["output"]["workouts_dir"])

            summary_rows.append(
                {
                    "video_id": video_id,
                    "title": title,
                    "url": metadata["url"],
                    "workout_type": workout_type,
                    "duration_minutes": metadata["duration_minutes"],
                    "intervals_count": len(intervals),
                    "status": status,
                    "review_reason": review_reason,
                }
            )

        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed processing %s", video_id)
            review_entries.append(f"{video_id}\terror: {exc}")

    write_summary_csv(summary_rows, config["output"]["summary_csv"])
    write_review_log(review_entries, config["output"]["review_log"])

    logger.info("Done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
