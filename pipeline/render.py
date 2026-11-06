"""FFmpeg renderer: 1080x1920 MP4 from b-roll + voiceover + burned-in captions."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

WIDTH, HEIGHT = 1080, 1920
FPS = 30
FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"


def probe_duration(path: Path) -> float:
    try:
        result = subprocess.run(
            [
                FFPROBE,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return float(result.stdout.strip() or 0.0)
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return 0.0


def run_ffmpeg(cmd: list[str]) -> None:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg not found — install it (apt install ffmpeg)") from exc
    if result.returncode != 0:
        printable = " ".join(shlex.quote(part) for part in cmd)
        raise RuntimeError(f"ffmpeg failed:\n{printable}\n{result.stderr[-4000:]}")


def _esc_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace("'", "\\'")


def caption_style(channel: dict) -> str:
    font = channel.get("caption_font") or "Noto Sans Devanagari"
    size = int(channel.get("caption_size", 20))
    margin = int(channel.get("caption_margin_v", 300))
    # NOTE: FontName must not contain a comma — it would break force_style parsing.
    return (
        f"FontName={font.replace(',', '')},FontSize={size},"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,"
        f"Outline=3,Shadow=0,Alignment=2,MarginV={margin},Bold=1"
    )


def _plan_segments(clips: list[Path], duration: float) -> list[tuple[Path, float]]:
    """Split the timeline across the available clips, looping them when short."""
    if not clips:
        return []
    per_clip = duration / len(clips)
    segments: list[tuple[Path, float]] = []
    total = 0.0
    index = 0
    while total < duration - 0.05 and index < 60:
        remaining = duration - total
        length = min(max(per_clip, 2.5), 8.0, remaining)
        if length < 0.8:
            length = remaining
        segments.append((clips[index % len(clips)], round(length, 3)))
        total += length
        index += 1
    return segments


def render_video(
    *,
    out_path: Path,
    duration: float,
    voice_path: Path | None = None,
    music_path: Path | None = None,
    srt_path: Path | None = None,
    clips: list[Path] | None = None,
    channel: dict | None = None,
    background: str = "0x0B0F17",
) -> Path:
    channel = channel or {}
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    duration = max(3.0, round(float(duration), 3))

    usable_clips = [Path(c) for c in (clips or []) if Path(c).exists()]
    segments = _plan_segments(usable_clips, duration)

    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error"]
    input_count = 0

    for clip, length in segments:
        # loop the clip and cut it with the trim filter (safer than an input -t)
        cmd += ["-stream_loop", "-1", "-i", str(clip)]
        input_count += 1

    if not segments:
        cmd += [
            "-f",
            "lavfi",
            "-t",
            f"{duration:.3f}",
            "-i",
            f"color=c={background}:s={WIDTH}x{HEIGHT}:r={FPS}",
        ]
        input_count += 1

    video_count = input_count
    voice_index = music_index = None

    if voice_path and Path(voice_path).exists():
        cmd += ["-i", str(voice_path)]
        voice_index = input_count
        input_count += 1

    if music_path and Path(music_path).exists():
        cmd += ["-stream_loop", "-1", "-i", str(music_path)]
        music_index = input_count
        input_count += 1

    if voice_index is None and music_index is None:
        # silent track so the mux never fails
        cmd += ["-f", "lavfi", "-t", f"{duration:.3f}", "-i", "anullsrc=r=44100:cl=stereo"]
        voice_index = input_count
        input_count += 1

    filters: list[str] = []
    for i in range(video_count):
        length = segments[i][1] if segments else duration
        filters.append(
            f"[{i}:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},setsar=1,fps={FPS},format=yuv420p,"
            f"trim=duration={length:.3f},setpts=PTS-STARTPTS[v{i}]"
        )

    if video_count == 1:
        filters.append("[v0]null[vcat]")
    else:
        joined = "".join(f"[v{i}]" for i in range(video_count))
        filters.append(f"{joined}concat=n={video_count}:v=1:a=0[vcat]")

    vout = "vcat"
    if srt_path and Path(srt_path).exists():
        filters.append(
            f"[{vout}]subtitles=f='{_esc_path(Path(srt_path))}':"
            f"force_style='{caption_style(channel)}'[vsub]"
        )
        vout = "vsub"

    if voice_index is not None:
        filters.append(
            f"[{voice_index}:a]aresample=44100,apad,atrim=0:{duration:.3f},"
            "asetpts=PTS-STARTPTS[a_voice]"
        )
    if music_index is not None:
        volume = float(channel.get("music_volume", 0.12))
        filters.append(
            f"[{music_index}:a]aresample=44100,volume={volume:.3f},"
            f"atrim=0:{duration:.3f},asetpts=PTS-STARTPTS[a_music]"
        )

    if voice_index is not None and music_index is not None:
        filters.append(
            "[a_voice][a_music]amix=inputs=2:duration=longest:normalize=0[a_out]"
        )
    elif voice_index is not None:
        filters.append("[a_voice]anull[a_out]")
    else:
        filters.append("[a_music]anull[a_out]")
    aout = "a_out"

    cmd += [
        "-filter_complex",
        ";".join(filters),
        "-map",
        f"[{vout}]",
        "-map",
        f"[{aout}]",
        "-t",
        f"{duration:.3f}",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "21",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-ar",
        "44100",
        "-movflags",
        "+faststart",
        str(out_path),
    ]
    run_ffmpeg(cmd)
    return out_path
