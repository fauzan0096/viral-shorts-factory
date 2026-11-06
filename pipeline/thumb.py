"""Thumbnail: a punchy vertical JPEG with a big headline burned in."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .config import ASSETS_DIR
from .render import FFMPEG, HEIGHT, WIDTH

FONT_CANDIDATES = [
    ASSETS_DIR / "fonts" / "NotoSansDevanagari-Bold.ttf",
    Path("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
]


def _font_file() -> str | None:
    for candidate in FONT_CANDIDATES:
        if candidate.exists():
            return str(candidate)
    fonts_dir = ASSETS_DIR / "fonts"
    if fonts_dir.exists():
        for found in sorted(fonts_dir.glob("*.[ot]tf")):
            return str(found)
    return None


def _esc(value: str) -> str:
    """Escape a value for a drawtext option (apostrophes become typographic)."""
    return (
        value.replace("\\", "/")
        .replace("'", "\u2019")
        .replace(":", "\\:")
        .replace("%", "\\%")
    )


def _wrap(text: str, limit: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= limit:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def make_thumbnail(
    out_path: Path,
    headline: str,
    channel: dict,
    video_path: Path | None = None,
) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    wrap = int(channel.get("thumb_wrap", 16))
    size = int(channel.get("thumb_size", 96))
    lines = _wrap(headline or "AAJ KA SACH", wrap)[:3]

    chain: list[str] = []
    if video_path and Path(video_path).exists():
        cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error"]
        cmd += ["-ss", "1", "-i", str(video_path)]
        chain.append(
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},eq=brightness=-0.12:saturation=1.15"
        )
    else:
        background = channel.get("thumb_bg", "0x0B0F17")
        cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error"]
        cmd += ["-f", "lavfi", "-i", f"color=c={background}:s={WIDTH}x{HEIGHT}"]

    font = _font_file()
    for index, line in enumerate(lines):
        y = 0.58 + index * 0.10
        options = [
            f"text='{_esc(line)}'",
            "expansion=none",
            "fontcolor=white",
            f"fontsize={size}",
            "borderw=8",
            "bordercolor=black",
            "x=(w-text_w)/2",
            f"y=h*{y:.3f}",
        ]
        if font:
            options.insert(0, f"fontfile='{_esc(font)}'")
        chain.append("drawtext=" + ":".join(options))

    if chain:
        cmd += ["-vf", ",".join(chain)]
    cmd += ["-frames:v", "1", "-q:v", "2", str(out_path)]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg not found — install it (apt install ffmpeg)") from exc
    if result.returncode != 0:
        raise RuntimeError(f"thumbnail failed:\n{result.stderr[-2000:]}")
    return out_path
