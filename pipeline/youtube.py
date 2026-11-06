"""Thin YouTube Data API v3 client built on the standard library only."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .config import env

API_BASE = "https://www.googleapis.com/youtube/v3"
TOKEN_URL = "https://oauth2.googleapis.com/token"
DEVICE_CODE_URL = "https://oauth2.googleapis.com/device/code"
UPLOAD_BASE = "https://www.googleapis.com/upload/youtube/v3/videos"
THUMBNAIL_URL = "https://www.googleapis.com/upload/youtube/v3/thumbnails/set"

SCOPES = "https://www.googleapis.com/auth/youtube.upload"


# --------------------------------------------------------------------------- #
# low level helpers
# --------------------------------------------------------------------------- #
def _request(
    url: str,
    *,
    data=None,
    headers: dict | None = None,
    method: str | None = None,
    timeout: int = 60,
):
    request = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            ctype = response.headers.get("Content-Type", "")
            if "json" in ctype:
                return json.loads(body.decode("utf-8") or "{}")
            return {"raw": body}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"YouTube API error {exc.code}: {detail[:800]}") from exc


def _get(path: str, params: dict) -> dict:
    query = urllib.parse.urlencode(
        {k: v for k, v in params.items() if v not in (None, "")}
    )
    return _request(f"{API_BASE}/{path}?{query}")


def _rfc3339(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(ts: str) -> datetime:
    cleaned = ts.replace("Z", "+00:00")
    if "." in cleaned:
        head, _, tail = cleaned.partition(".")
        cleaned = head + tail[tail.find("+") :] if "+" in tail else head + "+00:00"
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def api_key() -> str | None:
    return env("YOUTUBE_API_KEY")


# --------------------------------------------------------------------------- #
# discovery
# --------------------------------------------------------------------------- #
def most_popular(
    region_code: str = "IN",
    category_id: str | None = None,
    max_results: int = 40,
) -> list[dict]:
    key = api_key()
    if not key:
        return []
    payload = _get(
        "videos",
        {
            "part": "snippet,statistics",
            "chart": "mostPopular",
            "regionCode": region_code,
            "videoCategoryId": category_id,
            "maxResults": min(50, max_results),
            "key": key,
        },
    )
    return payload.get("items", [])


def search_recent(
    query: str,
    *,
    days: int = 7,
    max_results: int = 15,
    region_code: str = "IN",
) -> list[dict]:
    key = api_key()
    if not key:
        return []
    published_after = _rfc3339(datetime.now(timezone.utc) - timedelta(days=days))
    payload = _get(
        "search",
        {
            "part": "snippet",
            "q": query,
            "type": "video",
            "order": "viewCount",
            "publishedAfter": published_after,
            "regionCode": region_code,
            "maxResults": min(50, max_results),
            "key": key,
        },
    )
    return payload.get("items", [])


def videos_by_ids(ids: list[str]) -> list[dict]:
    key = api_key()
    if not key or not ids:
        return []
    payload = _get(
        "videos",
        {
            "part": "snippet,statistics",
            "id": ",".join(ids[:50]),
            "key": key,
        },
    )
    return payload.get("items", [])


# --------------------------------------------------------------------------- #
# auth (OAuth refresh token flow)
# --------------------------------------------------------------------------- #
def _credential(name: str, suffix: str | None) -> str | None:
    """Per-channel override: YOUTUBE_REFRESH_TOKEN_FACTS falls back to YOUTUBE_REFRESH_TOKEN."""
    if suffix:
        value = env(f"{name}_{suffix.strip().upper()}")
        if value:
            return value
    return env(name)


def access_token(suffix: str | None = None) -> str:
    client_id = _credential("YOUTUBE_CLIENT_ID", suffix)
    client_secret = _credential("YOUTUBE_CLIENT_SECRET", suffix)
    refresh_token = _credential("YOUTUBE_REFRESH_TOKEN", suffix)
    if not all([client_id, client_secret, refresh_token]):
        hint = f" (channel suffix '{suffix}')" if suffix else ""
        raise RuntimeError(
            "YouTube upload credentials missing"
            + hint
            + ". Set YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET and "
            "YOUTUBE_REFRESH_TOKEN (see docs/SETUP.md)."
        )
    body = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    ).encode()
    result = _request(
        TOKEN_URL,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    token = result.get("access_token")
    if not token:
        raise RuntimeError(f"Could not refresh YouTube token: {result}")
    return token


# --------------------------------------------------------------------------- #
# upload
# --------------------------------------------------------------------------- #
def upload_video(
    file_path: Path,
    *,
    title: str,
    description: str,
    tags: list[str],
    category_id: str | int,
    privacy: str = "private",
    publish_at: str | None = None,
    made_for_kids: bool = False,
    language: str = "en",
    thumbnail: Path | None = None,
    credential_suffix: str | None = None,
) -> dict:
    token = access_token(credential_suffix)
    file_path = Path(file_path)
    size = file_path.stat().st_size

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:4900],
            "tags": [t for t in tags if t][:30],
            "defaultLanguage": language,
            "defaultAudioLanguage": language,
        },
        "status": {
            "privacyStatus": "private" if publish_at else privacy,
            "selfDeclaredMadeForKids": bool(made_for_kids),
        },
    }
    if publish_at:
        # YouTube only accepts publishAt on private videos.
        body["status"]["publishAt"] = publish_at

    init = urllib.request.Request(
        f"{UPLOAD_BASE}?uploadType=resumable&part=snippet,status",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Length": str(size),
            "X-Upload-Content-Type": "video/mp4",
        },
        method="POST",
    )
    with urllib.request.urlopen(init, timeout=60) as response:
        location = response.headers.get("Location")
    if not location:
        raise RuntimeError("Could not create an upload session")

    with file_path.open("rb") as handle:
        put = urllib.request.Request(
            location,
            data=handle,
            headers={"Content-Type": "video/mp4", "Content-Length": str(size)},
            method="PUT",
        )
        with urllib.request.urlopen(put, timeout=900) as response:
            result = json.loads(response.read().decode("utf-8"))

    video_id = result.get("id")
    if thumbnail and video_id and Path(thumbnail).exists():
        set_thumbnail(video_id, Path(thumbnail), token)
    return result


def set_thumbnail(video_id: str, image_path: Path, token: str) -> None:
    data = Path(image_path).read_bytes()
    request = urllib.request.Request(
        f"{THUMBNAIL_URL}?videoId={video_id}",
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "image/jpeg",
            "Content-Length": str(len(data)),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120):
            return
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"Thumbnail upload failed: {detail[:500]}") from exc
