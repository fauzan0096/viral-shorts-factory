"""Trend radar: what is blowing up on YouTube right now, scored for Shorts."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from . import youtube

STOPWORDS = {
    # english
    "the", "and", "for", "with", "that", "this", "from", "your", "you", "are",
    "was", "were", "have", "has", "had", "not", "but", "all", "can", "will",
    "just", "how", "why", "what", "when", "who", "new", "now", "day", "days",
    "video", "shorts", "short", "best", "top", "vs", "about", "into", "his",
    "her", "its", "out", "one", "two", "get", "got", "make", "made", "more",
    # hindi / hinglish filler
    "hai", "hain", "hoga", "hogi", "kaise", "kya", "karo", "kare", "karein",
    "kar", "ka", "ki", "ke", "ko", "se", "me", "mein", "par", "aur", "ya",
    "nahi", "nahin", "bhi", "to", "toh", "jo", "wo", "woh", "ye", "yeh", "ek",
    "karne", "karna", "liye", "sab", "ab", "ho", "hum", "tum", "aap", "main",
    "apna", "apni", "bana", "banane", "batao", "suno", "dekho", "shortvideo",
}


@dataclass
class Signal:
    title: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    hours_old: float = 0.0
    source: str = ""
    video_id: str = ""

    @property
    def score(self) -> float:
        views_per_hour = self.views / max(self.hours_old, 1.0)
        engagement = (self.likes + 2 * self.comments) / max(self.views, 1)
        freshness = 1.0 if self.hours_old <= 96 else (0.8 if self.hours_old <= 240 else 0.5)
        return round(math.log10(views_per_hour + 10) * (1 + 20 * engagement) * freshness, 3)


@dataclass
class TrendReport:
    signals: list[Signal] = field(default_factory=list)
    source: str = "offline"

    def top(self, limit: int = 20) -> list[Signal]:
        return sorted(self.signals, key=lambda s: s.score, reverse=True)[:limit]


def _to_signal(item: dict, source: str) -> Signal:
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    raw_id = item.get("id")
    video_id = raw_id if isinstance(raw_id, str) else (raw_id or {}).get("videoId", "")
    published = snippet.get("publishedAt")
    hours_old = 0.0
    if published:
        try:
            moment = youtube.parse_iso(published)
            hours_old = max(
                0.0, (datetime.now(timezone.utc) - moment).total_seconds() / 3600.0
            )
        except Exception:
            hours_old = 0.0
    return Signal(
        title=snippet.get("title", ""),
        views=int(stats.get("viewCount", 0) or 0),
        likes=int(stats.get("likeCount", 0) or 0),
        comments=int(stats.get("commentCount", 0) or 0),
        hours_old=hours_old,
        source=source,
        video_id=video_id,
    )


def collect(channel: dict, *, log=print) -> TrendReport:
    """Pull trending + niche videos. Degrades to offline mode without an API key."""
    if not youtube.api_key():
        log("      no YOUTUBE_API_KEY -> offline mode (seed ideas only)")
        return TrendReport(signals=[], source="offline")

    signals: list[Signal] = []
    try:
        for item in youtube.most_popular(
            region_code=channel.get("region_code", "IN"),
            category_id=str(channel.get("category_id") or "") or None,
            max_results=30,
        ):
            signals.append(_to_signal(item, "trending"))
    except Exception as exc:  # API errors should never stop the pipeline
        log(f"      trend chart failed: {exc}")

    for query in channel.get("topic_queries") or []:
        try:
            for item in youtube.search_recent(
                query,
                days=10,
                max_results=8,
                region_code=channel.get("region_code", "IN"),
            ):
                signals.append(_to_signal(item, f"search:{query}"))
        except Exception as exc:
            log(f"      search '{query}' failed: {exc}")

    # search results carry no view counts -> hydrate them
    missing = [s for s in signals if s.views == 0 and s.video_id]
    if missing:
        try:
            details = {item["id"]: item for item in youtube.videos_by_ids([s.video_id for s in missing])}
        except Exception as exc:
            details = {}
            log(f"      stats lookup failed: {exc}")
        for signal in missing:
            item = details.get(signal.video_id)
            if not item:
                continue
            stats = item.get("statistics", {})
            signal.views = int(stats.get("viewCount", 0) or 0)
            signal.likes = int(stats.get("likeCount", 0) or 0)
            signal.comments = int(stats.get("commentCount", 0) or 0)

    signals = [s for s in signals if s.title and s.views > 0]
    source = "youtube-api" if signals else "offline"
    return TrendReport(signals=signals, source=source)


def keywords(report: TrendReport, limit: int = 12) -> list[tuple[str, float]]:
    """Weighted keywords from the winning titles — this is the 'viral signal'."""
    weights: dict[str, float] = {}
    for signal in report.top(30):
        seen: set[str] = set()
        for word in re.split(r"[^0-9A-Za-z\u0900-\u097F]+", signal.title.lower()):
            if len(word) < 4 or word in STOPWORDS or word.isdigit() or word in seen:
                continue
            seen.add(word)
            weights[word] = weights.get(word, 0.0) + signal.score
    ranked = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)
    return [(word, round(weight, 2)) for word, weight in ranked[:limit]]
