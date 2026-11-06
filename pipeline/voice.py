"""Voiceover: edge-tts (free, neural, Hindi voices) with word-timed captions."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from .captions import estimate_srt
from .render import probe_duration


@dataclass
class VoiceResult:
    audio: Path | None
    srt: Path | None
    duration: float
    real: bool

    @property
    def info(self) -> str:
        return "edge-tts" if self.real else "captions-only (no TTS)"


def available() -> bool:
    try:
        import edge_tts  # noqa: F401

        return True
    except Exception:
        return False


def synthesize(text: str, channel: dict, out_dir: Path) -> VoiceResult:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    mp3 = out_dir / "voice.mp3"
    srt = out_dir / "captions.srt"
    words_per_second = float(channel.get("words_per_second", 2.6) or 2.6)
    text = (text or "").strip()

    if text and channel.get("voice") and available():
        try:
            _edge(text, channel, mp3, srt)
            duration = probe_duration(mp3)
            if duration > 0 and srt.exists():
                return VoiceResult(mp3, srt, duration, True)
        except Exception as exc:  # noqa: BLE001 - never kill the run for TTS
            print(f"[voice] edge-tts failed, falling back: {exc}")

    duration = max(8.0, len(text.split()) / max(words_per_second, 0.5))
    if text:
        estimate_srt(text, words_per_second, srt)
        return VoiceResult(None, srt, duration, False)
    return VoiceResult(None, None, duration, False)


def _edge(text: str, channel: dict, mp3: Path, srt: Path) -> None:
    import edge_tts

    voice = channel.get("voice") or "hi-IN-MadhurNeural"
    rate = channel.get("voice_rate") or "+0%"

    async def _run() -> None:
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        submaker = edge_tts.SubMaker()
        with mp3.open("wb") as handle:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    handle.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    submaker.feed(chunk)
        srt.write_text(submaker.get_srt(), encoding="utf-8")

    asyncio.run(_run())
