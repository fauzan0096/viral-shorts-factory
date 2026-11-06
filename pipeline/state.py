"""Tiny JSON state store: used topics + published videos, per channel."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .config import work_dir


class State:
    def __init__(self, channel_id: str, path: Path | None = None) -> None:
        self.channel_id = channel_id
        self.path = path or (work_dir() / "state.json")
        self.data: dict = {"channels": {}}
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self.data = {"channels": {}}
        self.data.setdefault("channels", {})
        self.bucket = self.data["channels"].setdefault(
            channel_id, {"topics": {}, "videos": []}
        )
        self.bucket.setdefault("topics", {})
        self.bucket.setdefault("videos", [])

    # -- topics -------------------------------------------------------------
    def seen(self, key: str) -> bool:
        return key in self.bucket["topics"]

    def remember(self, key: str, topic: str) -> None:
        self.bucket["topics"][key] = {
            "topic": topic,
            "at": datetime.now().isoformat(timespec="seconds"),
        }
        self.save()

    def recent_topics(self, limit: int = 10) -> list[str]:
        items = sorted(
            self.bucket["topics"].items(),
            key=lambda kv: kv[1].get("at", ""),
            reverse=True,
        )
        return [v.get("topic", k) for k, v in items[:limit]]

    # -- videos -------------------------------------------------------------
    def add_video(self, record: dict) -> None:
        record = dict(record)
        record.setdefault("at", datetime.now().isoformat(timespec="seconds"))
        self.bucket["videos"].append(record)
        self.save()

    def video_count(self) -> int:
        return len(self.bucket["videos"])

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
