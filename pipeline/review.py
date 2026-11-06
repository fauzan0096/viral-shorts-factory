"""Human-readable run report (work/<channel>/<date>/review.md)."""

from __future__ import annotations

from pathlib import Path


def write(payload: dict, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append(f"# {payload.get('channel', 'run')} — {payload.get('date', '')}")
    lines.append("")
    lines.append(f"- Mode: **{payload.get('mode', '-')}**")
    lines.append(f"- Trend source: **{payload.get('trend_source', '-')}**")
    lines.append(f"- Idea: **{payload.get('idea', '-')}**")
    lines.append(f"- Voice: {payload.get('voice', '-')}")
    lines.append(f"- Duration: {payload.get('duration', '-')}")
    lines.append("")

    if payload.get("trend_evidence"):
        lines.append("## Trend evidence")
        for item in payload["trend_evidence"]:
            lines.append(f"- {item}")
        lines.append("")

    if payload.get("shortlist"):
        lines.append("## Shortlist")
        for row in payload["shortlist"]:
            marker = "**→**" if row.get("chosen") else "-"
            evidence = ""
            if row.get("evidence"):
                evidence = f"  _(ref: {row['evidence'][0]})_"
            lines.append(
                f"{marker} `{row.get('score', 0):.2f}` {row.get('topic', '')}{evidence}"
            )
        lines.append("")

    if payload.get("script"):
        script = payload["script"]
        lines.append("## Script")
        lines.append(f"**Hook:** {script.get('hook', '')}")
        lines.append("")
        for line in script.get("lines", []):
            lines.append(f"- {line}")
        if script.get("cta"):
            lines.append("")
            lines.append(f"**CTA:** {script['cta']}")
        lines.append("")

    if payload.get("meta"):
        meta = payload["meta"]
        lines.append("## Upload package")
        lines.append(f"- Title: {meta.get('title', '')}")
        lines.append(f"- Tags: {', '.join(meta.get('tags', [])[:12])}")
        lines.append(f"- Thumbnail text: {meta.get('thumbnail_headline', '')}")
        lines.append("")
        lines.append("### Description")
        lines.append("")
        lines.append("```")
        lines.append(meta.get("description", ""))
        lines.append("```")
        lines.append("")

    if payload.get("files"):
        lines.append("## Files")
        for label, value in payload["files"].items():
            if value:
                lines.append(f"- {label}: `{value}`")
        lines.append("")

    if payload.get("upload"):
        upload = payload["upload"]
        lines.append("## Upload")
        lines.append(f"- {upload.get('url') or 'not uploaded'} ({upload.get('privacy', '-')})")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
