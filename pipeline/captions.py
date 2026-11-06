"""SRT captions. Edge-TTS gives word timings; without it we estimate from WPS."""

from __future__ import annotations

import re
from pathlib import Path


def _timestamp(seconds: float) -> str:
    seconds = max(0.0, seconds)
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    whole = int(secs)
    millis = int(round((secs - whole) * 1000))
    if millis == 1000:
        whole += 1
        millis = 0
    return f"{int(hours):02d}:{int(minutes):02d}:{whole:02d},{millis:03d}"


def estimate_srt(
    text: str,
    words_per_second: float,
    path: Path,
    *,
    max_words: int = 5,
) -> Path:
    words = [w for w in re.split(r"\s+", (text or "").strip()) if w]
    wps = max(0.5, float(words_per_second or 2.6))

    lines: list[str] = []
    index = 1
    for start in range(0, len(words), max_words):
        chunk = words[start : start + max_words]
        begin = start / wps
        end = (start + len(chunk)) / wps
        lines.append(f"{index}\n{_timestamp(begin)} --> {_timestamp(end)}\n{' '.join(chunk)}\n")
        index += 1

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
