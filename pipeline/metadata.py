"""Title / description / tags for upload, built from the script."""

from __future__ import annotations

import re

from .ideas import Idea
from .script import Script

GENERIC_TAGS = ["shorts", "youtube shorts", "viral", "trending", "hindi"]


def build(script: Script, idea: Idea, channel: dict) -> dict:
    topic = script.topic or idea.topic
    hashtags = [tag if tag.startswith("#") else f"#{tag}" for tag in channel.get("hashtags") or []]

    title = _title(topic, channel)
    description = _description(script, topic, channel, hashtags)
    tags = _tags(topic, channel, hashtags)
    headline = _headline(topic, channel)

    return {
        "title": title,
        "description": description,
        "tags": tags,
        "hashtags": hashtags,
        "thumbnail_headline": headline,
        "category_id": str(channel.get("category_id", "27")),
        "language": channel.get("language", "hi"),
    }


def _title(topic: str, channel: dict) -> str:
    suffix = " | #shorts"
    room = 100 - len(suffix)
    topic = (topic or "aaj ka sach").strip()
    if len(topic) > room:
        topic = topic[: room - 1].rstrip() + "…"
    return topic + suffix


def _description(script: Script, topic: str, channel: dict, hashtags: list[str]) -> str:
    parts = [topic]
    body = " ".join(script.lines[:3]).strip()
    if body:
        parts.append(body)
    cta = (script.cta or "").strip()
    if cta:
        parts.append(cta)
    if hashtags:
        parts.append(" ".join(hashtags[:8]))
    parts.append(
        f"Roz ek nayi video — {channel.get('name', 'our channel')}.\n"
        "Content original hai; footage stock/licensed use hui hai."
    )
    return "\n\n".join(parts)[:4900]


def _tags(topic: str, channel: dict, hashtags: list[str]) -> list[str]:
    words = [
        w
        for w in re.split(r"[^0-9A-Za-z\u0900-\u097F]+", topic.lower())
        if len(w) > 2
    ]
    tags = [tag.lstrip("#") for tag in hashtags]
    tags += words
    tags += str(channel.get("name", "")).split()
    tags += GENERIC_TAGS
    seen: set[str] = set()
    clean: list[str] = []
    for tag in tags:
        tag = tag.strip()
        if tag and tag.lower() not in seen:
            seen.add(tag.lower())
            clean.append(tag)
    return clean[:30]


def _headline(topic: str, channel: dict) -> str:
    custom = (channel.get("thumb_headline") or "").strip()
    if custom:
        return custom
    words = (topic or "aaj ka sach").split()
    return " ".join(words[:5]).upper()
