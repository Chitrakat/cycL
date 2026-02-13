from __future__ import annotations

from typing import Any

from googleapiclient.discovery import build

from cycling_workout_extractor.utils import parse_iso8601_duration


def build_youtube_client(api_key: str) -> Any:
    return build("youtube", "v3", developerKey=api_key)


def fetch_playlist_video_ids(youtube: Any, playlist_id: str) -> list[str]:
    video_ids: list[str] = []
    page_token = None

    while True:
        response = (
            youtube.playlistItems()
            .list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=page_token,
            )
            .execute()
        )

        for item in response.get("items", []):
            content = item.get("contentDetails", {})
            video_id = content.get("videoId")
            if video_id:
                video_ids.append(video_id)

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return video_ids


def fetch_video_metadata(youtube: Any, video_id: str) -> dict[str, Any] | None:
    response = (
        youtube.videos()
        .list(part="snippet,contentDetails", id=video_id)
        .execute()
    )

    items = response.get("items", [])
    if not items:
        return None

    item = items[0]
    snippet = item.get("snippet", {})
    content_details = item.get("contentDetails", {})

    duration_seconds = parse_iso8601_duration(content_details.get("duration", ""))
    duration_minutes = int(round(duration_seconds / 60)) if duration_seconds else 0

    return {
        "video_id": video_id,
        "title": snippet.get("title", ""),
        "description": snippet.get("description", ""),
        "duration_seconds": duration_seconds,
        "duration_minutes": duration_minutes,
        "url": f"https://www.youtube.com/watch?v={video_id}",
    }
