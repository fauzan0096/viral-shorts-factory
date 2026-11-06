"""Upload wrapper: decides privacy, calls the API, returns what to log."""

from __future__ import annotations

from pathlib import Path

from . import youtube


def publish(
    video_path: Path,
    meta: dict,
    channel: dict,
    privacy: str = "private",
    *,
    thumbnail: Path | None = None,
    publish_at: str | None = None,
    log=print,
) -> dict:
    result = youtube.upload_video(
        video_path,
        title=meta["title"],
        description=meta["description"],
        tags=meta["tags"],
        category_id=meta["category_id"],
        privacy=privacy,
        publish_at=publish_at,
        language=meta.get("language", "en"),
        thumbnail=thumbnail,
        credential_suffix=channel.get("credential_suffix") or None,
    )
    video_id = result.get("id")
    log(f"      uploaded: https://youtu.be/{video_id} ({privacy})")
    return {
        "video_id": video_id,
        "url": f"https://youtu.be/{video_id}" if video_id else None,
        "privacy": privacy,
        "publish_at": publish_at,
    }
