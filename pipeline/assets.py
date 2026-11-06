"""B-roll and music. Local library first, optional Pexels download as a refill."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .config import ASSETS_DIR, env

VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}
AUDIO_EXTS = (".mp3", ".m4a", ".wav", ".aac", ".ogg")
PEXELS_SEARCH = "https://api.pexels.com/videos/search"


def local_broll(limit: int = 12) -> list[Path]:
    folder = ASSETS_DIR / "broll"
    if not folder.exists():
        return []
    files = sorted(
        p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXT
    )
    return files[:limit]


def music_path(name: str | None) -> Path | None:
    folder = ASSETS_DIR / "music"
    if not folder.exists():
        return None
    if name:
        candidate = folder / name
        if candidate.exists():
            return candidate
    for path in sorted(folder.iterdir()):
        if path.suffix.lower() in AUDIO_EXTS:
            return path
    return None


def fetch_broll(queries: list[str], out_dir: Path, *, count: int = 3, log=print) -> list[Path]:
    """Download portrait stock clips from Pexels (needs a free API key)."""
    key = env("PEXELS_API_KEY")
    if not key or not queries:
        return []
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    downloaded: list[Path] = []
    for query in queries:
        if len(downloaded) >= count:
            break
        try:
            links = _search(key, query)
        except Exception as exc:  # noqa: BLE001
            log(f"      pexels search '{query}' failed: {exc}")
            continue
        for link in links:
            if len(downloaded) >= count:
                break
            target = out_dir / f"broll-{len(downloaded) + 1}.mp4"
            temp = out_dir / "download.tmp"
            try:
                urllib.request.urlretrieve(link, temp)
                temp.replace(target)
                downloaded.append(target)
            except Exception as exc:  # noqa: BLE001
                log(f"      b-roll download failed: {exc}")
                temp.unlink(missing_ok=True)
    return downloaded


def _search(key: str, query: str, per_page: int = 12) -> list[str]:
    params = urllib.parse.urlencode(
        {
            "query": query,
            "orientation": "portrait",
            "per_page": per_page,
            "size": "medium",
        }
    )
    request = urllib.request.Request(
        f"{PEXELS_SEARCH}?{params}",
        headers={"Authorization": key, "User-Agent": "viral-shorts-factory"},
    )
    with urllib.request.urlopen(request, timeout=40) as response:
        payload = json.loads(response.read().decode("utf-8"))

    links: list[str] = []
    for video in payload.get("videos", []):
        best = _best_file(video.get("video_files", []))
        if best:
            links.append(best)
    return links


def _best_file(files: list[dict]) -> str | None:
    portrait = [
        f
        for f in files
        if f.get("file_type") == "video/mp4"
        and (f.get("height") or 0) >= (f.get("width") or 0)
        and (f.get("width") or 0) >= 540
    ]
    pool = portrait or [f for f in files if f.get("file_type") == "video/mp4"]
    if not pool:
        return None
    pool.sort(key=lambda f: (f.get("width") or 0))
    # smallest portrait file that is still HD-ish keeps CI fast
    for candidate in pool:
        if (candidate.get("width") or 0) >= 720:
            return candidate.get("link")
    return pool[0].get("link")
