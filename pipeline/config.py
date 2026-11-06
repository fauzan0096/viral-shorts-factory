"""Configuration: .env loading, channel profiles, work directories."""

from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANNELS_DIR = ROOT / "channels"
ASSETS_DIR = ROOT / "assets"
DEFAULT_WORK_DIR = ROOT / "work"

CHANNEL_DEFAULTS: dict = {
    "id": "",
    # agar ye channel ka YouTube account alag hai to suffix do (e.g. "FACTS"),
    # phir secrets YOUTUBE_REFRESH_TOKEN_FACTS / _CLIENT_ID_FACTS / _CLIENT_SECRET_FACTS
    "credential_suffix": "",
    "name": "",
    "language": "hi",
    "duration_target": 38,
    # --- voice ---
    "voice": "hi-IN-MadhurNeural",
    "voice_rate": "+8%",
    "words_per_second": 2.6,
    # --- trends ---
    "region_code": "IN",
    "category_id": "27",
    "topic_queries": [],
    # --- video ---
    "broll_queries": [],
    "music": None,
    "music_volume": 0.12,
    "caption_font": "Noto Sans Devanagari",
    "caption_size": 20,
    "caption_margin_v": 300,
    # --- thumbnail ---
    "thumb_wrap": 16,
    "thumb_size": 96,
    # --- content ---
    "hooks": [],
    "line_bank": [],
    "idea_templates": [],
    "seed_ideas": [],
    "cta": "",
    "hashtags": [],
    "privacy": "private",
}


def load_env(path: Path | None = None) -> None:
    """Minimal .env reader (no python-dotenv dependency)."""
    env_path = path or ROOT / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def env(key: str, default: str | None = None) -> str | None:
    value = os.environ.get(key)
    if value is None or value == "":
        return default
    return value


def work_dir() -> Path:
    path = Path(env("WORK_DIR") or DEFAULT_WORK_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_channels() -> list[str]:
    if not CHANNELS_DIR.exists():
        return []
    return sorted(p.stem for p in CHANNELS_DIR.glob("*.json"))


def load_channel(channel_id: str) -> dict:
    path = CHANNELS_DIR / f"{channel_id}.json"
    if not path.exists():
        known = ", ".join(list_channels()) or "(none)"
        raise SystemExit(f"Channel '{channel_id}' not found. Available: {known}")
    data = json.loads(path.read_text(encoding="utf-8"))
    channel = dict(CHANNEL_DEFAULTS)
    channel.update({k: v for k, v in data.items() if v is not None})
    channel["id"] = channel_id
    channel.setdefault("name", channel_id)
    return channel


def slugify(text: str, max_len: int = 60) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return (text[:max_len] or "idea").strip("-")
