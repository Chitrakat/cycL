from __future__ import annotations

import re
from typing import Any

from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi

from cycling_workout_extractor.utils import (
    parse_timestamp_to_seconds,
    seconds_to_mmss,
)

POWER_PATTERNS = [
    re.compile(r"(?P<level>\d{1,2})\s*/\s*10"),
    re.compile(r"(?P<level>\d{1,2})\s*out\s*of\s*10"),
    re.compile(r"effort\s*level\s*(?P<level>\d{1,2})"),
]

CADENCE_PATTERNS = [
    re.compile(r"(?P<rpm>\d{2,3})\s*rpm"),
    re.compile(r"cadence\s*of\s*(?P<rpm>\d{2,3})"),
]

ZONE_KEYWORDS = {
    "warmup": "warmup",
    "warm up": "warmup",
    "main set": "main set",
    "recovery": "recovery",
    "cooldown": "cooldown",
    "cool down": "cooldown",
}

WORD_NUMBERS = {
    "ten": 10,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
}


def parse_description_timestamps(
    description: str, total_duration_seconds: int
) -> list[dict[str, Any]]:
    lines = [line.strip() for line in description.splitlines() if line.strip()]
    matches: list[tuple[int, str]] = []

    for line in lines:
        match = re.match(
            r"^(?P<ts>(?:\d{1,2}:)?\d{1,2}:\d{2})\s+(?P<text>.+)", line
        )
        if match:
            timestamp = match.group("ts")
            text = match.group("text").strip()
            start_seconds = parse_timestamp_to_seconds(timestamp)
            matches.append((start_seconds, text))

    intervals: list[dict[str, Any]] = []
    for idx, (start_seconds, text) in enumerate(matches):
        end_seconds = None
        if idx + 1 < len(matches):
            end_seconds = matches[idx + 1][0]
        elif total_duration_seconds:
            end_seconds = total_duration_seconds

        interval = _build_interval(start_seconds, end_seconds, text)
        intervals.append(interval)

    return intervals


def parse_transcript_intervals(
    video_id: str, total_duration_seconds: int
) -> list[dict[str, Any]]:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
    except (TranscriptsDisabled, NoTranscriptFound):
        return []

    intervals: list[dict[str, Any]] = []
    for segment in transcript:
        text = segment.get("text", "")
        lower = text.lower()

        power = _extract_power(lower)
        cadence = _extract_cadence(lower)
        zone = _extract_zone(lower)

        if not (power or cadence or zone):
            continue

        start_seconds = int(segment.get("start", 0))
        duration_seconds = _extract_duration_override(lower)
        if duration_seconds is None:
            duration_seconds = int(segment.get("duration", 0))

        end_seconds = start_seconds + duration_seconds if duration_seconds else None
        if end_seconds and total_duration_seconds:
            end_seconds = min(end_seconds, total_duration_seconds)

        intervals.append(
            {
                "start_time": seconds_to_mmss(start_seconds),
                "end_time": seconds_to_mmss(end_seconds) if end_seconds else "",
                "duration_seconds": duration_seconds or 0,
                "power_level": power,
                "cadence_rpm": cadence,
                "zone": zone,
                "description": text.strip(),
            }
        )

    return intervals


def _build_interval(
    start_seconds: int, end_seconds: int | None, text: str
) -> dict[str, Any]:
    lower = text.lower()
    power = _extract_power(lower)
    cadence = _extract_cadence(lower)
    zone = _extract_zone(lower)

    duration_seconds = end_seconds - start_seconds if end_seconds else 0
    return {
        "start_time": seconds_to_mmss(start_seconds),
        "end_time": seconds_to_mmss(end_seconds) if end_seconds else "",
        "duration_seconds": duration_seconds,
        "power_level": power,
        "cadence_rpm": cadence,
        "zone": zone,
        "description": text.strip(),
    }


def _extract_power(text: str) -> str:
    for pattern in POWER_PATTERNS:
        match = pattern.search(text)
        if match:
            level = int(match.group("level"))
            return f"{level}/10"
    match = re.search(r"level\s*(\d{1,2})", text)
    if match:
        return f"{int(match.group(1))}/10"
    return ""


def _extract_cadence(text: str) -> int:
    for pattern in CADENCE_PATTERNS:
        match = pattern.search(text)
        if match:
            return int(match.group("rpm"))

    match = re.search(r"cadence\s*of\s*(?P<word>[a-z]+)", text)
    if match:
        word = match.group("word")
        if word in WORD_NUMBERS:
            return WORD_NUMBERS[word]

    word_match = re.search(r"(?P<word>[a-z]+)\s*rpm", text)
    if word_match:
        word = word_match.group("word")
        if word in WORD_NUMBERS:
            return WORD_NUMBERS[word]

    return 0


def _extract_zone(text: str) -> str:
    for keyword, zone in ZONE_KEYWORDS.items():
        if keyword in text:
            return zone
    return ""


def _extract_duration_override(text: str) -> int | None:
    match = re.search(
        r"(?:next|for the next|for)\s+(?P<value>\d+|[a-z]+)\s+"
        r"(?P<unit>seconds|second|minutes|minute)",
        text,
    )
    if not match:
        return None

    value_token = match.group("value")
    unit = match.group("unit")

    if value_token.isdigit():
        value = int(value_token)
    else:
        value = WORD_NUMBERS.get(value_token, 0)

    if not value:
        return None

    multiplier = 60 if "minute" in unit else 1
    return value * multiplier
