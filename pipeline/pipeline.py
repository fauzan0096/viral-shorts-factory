"""The daily run: trend -> idea -> script -> voice -> render -> thumbnail -> upload."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from . import assets, metadata, publish as publish_mod, render, review, script as script_mod
from . import ideas as ideas_mod
from . import thumb, trends, voice
from .config import load_channel, load_env, slugify, work_dir
from .state import State


def run(
    channel_id: str,
    *,
    dry_run: bool = False,
    upload_mode: str | None = None,
    idea_text: str | None = None,
    shortlist: int = 3,
    log=print,
) -> dict:
    load_env()
    channel = load_channel(channel_id)
    day = datetime.now().strftime("%Y-%m-%d")
    out_dir = work_dir() / channel["id"] / day
    out_dir.mkdir(parents=True, exist_ok=True)
    state = State(channel["id"])

    log(f"[1/8] trend radar — {channel.get('name') or channel_id}")
    report = trends.collect(channel, log=log)
    log(f"      {len(report.signals)} signals ({report.source})")

    log("[2/8] idea shortlist")
    pool = ideas_mod.shortlist(channel, report, state, count=max(3, int(shortlist)))
    if idea_text:
        manual = ideas_mod.Idea(
            key=slugify(f"manual-{idea_text}"),
            topic=idea_text.strip(),
            angle="manual",
            score=999.0,
        )
        pool = [manual] + [i for i in pool if i.key != manual.key]
    if not pool:
        raise SystemExit("Koi idea nahi mila — channels/*.json me seed_ideas bharo.")
    for index, candidate in enumerate(pool, 1):
        log(f"      {index}. [{candidate.score:6.2f}] {candidate.topic}")
    chosen = pool[0]
    log(f"      -> picked: {chosen.topic}")

    log("[3/8] script")
    script = script_mod.write(chosen, channel, log=log)
    log(f"      {script.word_count} words ({script.source})")
    script_path = out_dir / "script.txt"
    script_path.write_text(script.spoken + "\n", encoding="utf-8")

    package = metadata.build(script, chosen, channel)

    payload: dict = {
        "channel": channel.get("name") or channel_id,
        "date": day,
        "mode": "dry-run" if dry_run else "full",
        "trend_source": report.source,
        "idea": chosen.topic,
        "shortlist": [
            {
                "topic": idea.topic,
                "score": idea.score,
                "evidence": idea.evidence,
                "chosen": idea.key == chosen.key,
            }
            for idea in pool
        ],
        "trend_evidence": [f"{s.title}  ({s.views:,} views, score {s.score})" for s in report.top(8)],
        "script": {
            "hook": script.hook,
            "lines": script.lines,
            "cta": script.cta,
            "source": script.source,
        },
        "meta": package,
        "files": {"script": str(script_path)},
    }

    if dry_run:
        payload["voice"] = "skipped (dry-run)"
        payload["duration"] = f"{channel.get('duration_target')}s target"
        path = review.write(payload, out_dir / "review.md")
        log(f"[dry-run] review likh diya: {path}")
        return {"mode": "dry-run", "review": str(path), "idea": chosen.topic, "meta": package}

    log("[4/8] voice")
    result = voice.synthesize(script.spoken, channel, out_dir)
    duration = round(result.duration + 0.4, 3)
    log(f"      {result.info}, {duration:.1f}s")
    payload["voice"] = result.info
    payload["duration"] = f"{duration:.1f}s"

    log("[5/8] footage")
    clips = assets.local_broll()
    if not clips:
        clips = assets.fetch_broll(channel.get("broll_queries") or [], out_dir, log=log)
    music = assets.music_path(channel.get("music"))
    log(f"      {len(clips)} clip(s){', music' if music else ', no music'}")

    log("[6/8] render")
    video_path = out_dir / "video.mp4"
    render.render_video(
        out_path=video_path,
        duration=duration,
        voice_path=result.audio,
        music_path=music,
        srt_path=result.srt,
        clips=clips,
        channel=channel,
    )
    log(f"      {video_path} ({video_path.stat().st_size / 1_048_576:.1f} MB)")

    log("[7/8] thumbnail")
    thumbnail_path = thumb.make_thumbnail(
        out_dir / "thumbnail.jpg",
        package["thumbnail_headline"],
        channel,
        video_path=video_path,
    )

    payload["files"].update(
        {
            "video": str(video_path),
            "thumbnail": str(thumbnail_path),
            "captions": str(result.srt) if result.srt else None,
            "music": str(music) if music else None,
        }
    )

    mode = (upload_mode or channel.get("privacy") or "private").lower()
    upload_result = None
    if mode in {"none", "skip", "no"}:
        log("[8/8] upload skipped")
    else:
        log(f"[8/8] upload ({mode})")
        try:
            upload_result = publish_mod.publish(
                video_path, package, channel, mode, thumbnail=thumbnail_path, log=log
            )
        except Exception as exc:  # noqa: BLE001 - keep the rendered video
            log(f"      upload failed: {exc}")
            upload_result = {"error": str(exc), "privacy": mode}

    payload["upload"] = upload_result or {"privacy": "skipped"}
    path = review.write(payload, out_dir / "review.md")

    state.remember(chosen.key, chosen.topic)
    state.add_video(
        {
            "topic": chosen.topic,
            "video": str(video_path),
            "thumbnail": str(thumbnail_path),
            "upload": upload_result,
        }
    )

    log(f"done — report: {path}")
    return {
        "mode": mode,
        "idea": chosen.topic,
        "video": str(video_path),
        "thumbnail": str(thumbnail_path),
        "review": str(path),
        "upload": upload_result,
        "meta": package,
    }
