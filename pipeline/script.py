"""Script writing: LLM when a key exists, curated template bank otherwise."""

from __future__ import annotations

import json
import random
import re
import urllib.request
from dataclasses import dataclass, field

from .config import env
from .ideas import Idea

SYSTEM_PROMPT = (
    "You write 30-45 second vertical videos (YouTube Shorts / Reels) in casual "
    "Hinglish. Rules: one punchy hook in the first 6 words, short spoken lines, "
    "no emojis, no hashtags, no stage directions, no quotes around the text. "
    "Answer with strict JSON: {\"hook\": str, \"lines\": [str], \"cta\": str}."
)


@dataclass
class Script:
    topic: str
    hook: str
    lines: list[str] = field(default_factory=list)
    cta: str = ""
    source: str = "template"

    @property
    def spoken(self) -> str:
        parts = [self.hook, *self.lines, self.cta]
        return " ".join(p.strip() for p in parts if p and p.strip())

    @property
    def word_count(self) -> int:
        return len(self.spoken.split())


def write(idea: Idea, channel: dict, *, log=print) -> Script:
    budget = max(28, int(float(channel.get("duration_target", 38)) * float(channel.get("words_per_second", 2.6))))
    from_llm = _llm(idea, channel, budget)
    if from_llm:
        return from_llm
    return _template(idea, channel, budget)


# --------------------------------------------------------------------------- #
# template fallback — works with zero API keys
# --------------------------------------------------------------------------- #
def _template(idea: Idea, channel: dict, budget: int) -> Script:
    rng = random.Random(f"{channel.get('id')}:{idea.key}")
    hooks = channel.get("hooks") or ["{topic} — 30 second me ek sach."]
    hook = rng.choice(hooks).format(topic=idea.topic).strip()

    bank = [line.strip() for line in (channel.get("line_bank") or []) if line.strip()]
    rng.shuffle(bank)

    lines: list[str] = []
    used = len(hook.split())
    for line in bank:
        if used >= budget - 8:
            break
        if line in lines:
            continue
        lines.append(line)
        used += len(line.split())

    if not lines:
        lines = [f"{idea.topic} par sabse zaroori baat: roz thoda, lekin roz."]

    cta = (channel.get("cta") or "").strip()
    if cta and used + len(cta.split()) > budget + 12:
        cta = ""
    return Script(topic=idea.topic, hook=hook, lines=lines, cta=cta, source="template")


# --------------------------------------------------------------------------- #
# optional LLM path (any OpenAI-compatible endpoint)
# --------------------------------------------------------------------------- #
def _llm(idea: Idea, channel: dict, budget: int) -> Script | None:
    key = env("OPENAI_API_KEY")
    if not key:
        return None
    base = (env("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    model = env("SCRIPT_MODEL") or "gpt-4o-mini"

    prompt = (
        f"Topic: {idea.topic}\n"
        f"Angle: {idea.angle or 'practical, honest'}\n"
        f"Channel: {channel.get('name')} ({channel.get('language')})\n"
        f"Spoken budget: about {budget} words for hook + lines, cta max 12 words.\n"
        "Write it so a 40 second voiceover sounds natural when read out loud."
    )
    payload = {
        "model": model,
        "temperature": 0.85,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }
    try:
        request = urllib.request.Request(
            f"{base}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=90) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        data = _extract_json(content)
        hook = str(data.get("hook", "")).strip()
        lines = [str(line).strip() for line in data.get("lines", []) if str(line).strip()]
        cta = str(data.get("cta", "")).strip()
        if not hook or not lines:
            return None
        return Script(topic=idea.topic, hook=hook, lines=lines, cta=cta, source=f"llm:{model}")
    except Exception:
        return None


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"```\s*$", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no json in model answer")
    return json.loads(text[start : end + 1])
