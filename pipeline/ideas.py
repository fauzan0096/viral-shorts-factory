"""Turn trend signals into an original idea (never a copy of someone's video)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .config import slugify
from .trends import TrendReport, keywords

DEFAULT_TEMPLATES = ["{keyword} — ek sach jo sabko pata hona chahiye"]


@dataclass
class Idea:
    key: str
    topic: str
    angle: str = ""
    score: float = 0.0
    evidence: list[str] = field(default_factory=list)


def _words(text: str) -> set[str]:
    return {
        w
        for w in re.split(r"[^0-9A-Za-z\u0900-\u097F]+", text.lower())
        if len(w) > 3
    }


def _overlap(topic: str, title: str) -> bool:
    return bool(_words(topic) & _words(title))


def shortlist(
    channel: dict,
    report: TrendReport,
    state,
    *,
    count: int = 3,
) -> list[Idea]:
    """Return the best unused ideas, best first. Trend hits boost a topic's score."""
    kw = keywords(report)
    titles = [s.title for s in report.top(25)]
    kw_weight = dict(kw)

    candidates: list[Idea] = []

    # 1) evergreen seed ideas from the channel profile
    for topic in channel.get("seed_ideas") or []:
        key = slugify(topic)
        evidence = [t for t in titles if _overlap(topic, t)][:3]
        boost = sum(
            kw_weight.get(word, 0.0) for word in _words(topic) if word in kw_weight
        )
        candidates.append(
            Idea(
                key=key,
                topic=topic,
                angle=_angle(channel, topic),
                score=1.0 + boost + 0.5 * len(evidence),
                evidence=evidence,
            )
        )

    # 2) fresh ideas built from what is trending right now
    templates = channel.get("idea_templates") or DEFAULT_TEMPLATES
    for index, (word, weight) in enumerate(kw[:6]):
        topic = templates[index % len(templates)].format(keyword=word)
        candidates.append(
            Idea(
                key=slugify(f"trend-{word}"),
                topic=topic,
                angle="trend",
                score=2.0 + weight,
                evidence=[t for t in titles if _overlap(topic, t)][:3],
            )
        )

    # 3) de-dupe + drop anything already used
    unique: dict[str, Idea] = {}
    for idea in candidates:
        if not idea.topic.strip() or state.seen(idea.key):
            continue
        current = unique.get(idea.key)
        if current is None or idea.score > current.score:
            unique[idea.key] = idea

    ranked = sorted(unique.values(), key=lambda i: i.score, reverse=True)
    if not ranked:
        seeds = channel.get("seed_ideas") or []
        fallback = seeds[0] if seeds else "aaj ka sach"
        ranked = [
            Idea(
                key=slugify(f"repeat-{state.video_count()}-{fallback}"),
                topic=fallback,
                angle="repeat",
                score=0.5,
            )
        ]
    return ranked[: max(1, count)]


def _angle(channel: dict, topic: str) -> str:
    language = channel.get("language", "hi")
    if language.startswith("hi"):
        return f"short, seedhi baat — {topic}"
    return f"straight talk — {topic}"
