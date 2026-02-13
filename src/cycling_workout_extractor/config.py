from __future__ import annotations

import logging
import os
from typing import Any

import yaml
from dotenv import load_dotenv


def load_config(path: str) -> dict[str, Any]:
    load_dotenv()

    with open(path, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    config.setdefault("api", {})
    config.setdefault("playlists", [])
    config.setdefault("output", {})
    config.setdefault("classification", {})
    config.setdefault("non_workout_keywords", [])
    config.setdefault("parser", {})

    return config


def setup_logging(log_path: str) -> logging.Logger:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    logger = logging.getLogger("cycling_workout_extractor")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
