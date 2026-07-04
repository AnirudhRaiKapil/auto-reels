"""Generate a reel script + caption + hashtags with Gemini (free tier).

Falls back to a built-in offline topic bank if no API key is set,
so the pipeline never hard-fails.
"""
import json
import os
import random
import re

import config

FALLBACK = {
    "facts": [
        {
            "script": "Your bones are constantly being replaced. Every ten years, "
            "your skeleton is almost entirely new. Cells called osteoclasts break "
            "old bone down while osteoblasts build fresh bone in its place. "
            "That means the skeleton you have today is not the one you had a "
            "decade ago. Your body is quietly rebuilding you, all the time.",
            "title": "Your skeleton replaces itself every 10 years",
        },
    ],
    "motivation": [
        {
            "script": "You don't need motivation. You need a decision. Motivation "
            "shows up late and leaves early. Discipline shows up every single day. "
            "Start with five minutes. Just five. Because the hardest part was "
            "never the work. It was starting. And once you start, you're already "
            "ahead of the person you were yesterday.",
            "title": "You don't need motivation. You need this.",
        },
    ],
    "ai_news": [
        {
            "script": "AI models don't actually read words. They read tokens, tiny "
            "chunks of text turned into numbers. Every answer you get is the model "
            "predicting the next most likely token, billions of times per second. "
            "It sounds simple, but stack enough predictions together and you get "
            "essays, code, and conversations. Prediction, at scale, looks a lot "
            "like thinking.",
            "title": "How AI actually 'reads' your messages",
        },
    ],
}

PROMPT_TEMPLATE = """You are a short-form video scriptwriter whose scripts feel like a smart, \
curious friend talking - never like AI or a news anchor. Your scripts get \
rewatched because they contain real substance: specific numbers, names, \
places, and mechanisms, not vague filler.

TASK: {niche_prompt}

Angle for this one: {domain}.
Opening style: {hook_style}.

STYLE RULES (strict):
- Use contractions everywhere. Vary sentence length: some 3-word punches, some longer.
- Every claim must be concrete. Never "scientists say" - name who, where, when, how much.
- No rhetorical filler, no "isn't that amazing", no summarizing what you just said.
- NEVER use any of these phrases or close variants: {banned}
- The last line should feel like a natural thought, not a call to action.

Avoid these recently used topics: {recent_topics}

Respond ONLY with JSON in this exact shape:
{{
  "script": "the spoken script",
  "title": "a click-worthy title under 90 characters",
  "caption": "an Instagram caption, 1-2 sentences",
  "hashtags": ["#tag1", "#tag2", "... 10 relevant hashtags"],
  "broll": ["4 to 6 short stock-footage search phrases, in script order, each literally showing what that part of the script talks about, e.g. 'glacier collapsing ocean' or 'person running sunrise street'"]
}}"""


def _llm_text(prompt: str) -> str:
    """Generate text with Groq (free tier)."""
    import requests

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
        json={
            "model": config.GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.9,
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def generate(niche: str, recent_topics: list[str]) -> dict:
    if not config.GROQ_API_KEY:
        item = random.choice(FALLBACK[niche])
        return {
            "script": item["script"],
            "title": item["title"],
            "caption": item["title"],
            "hashtags": ["#shorts", "#reels", "#" + niche.replace("_", "")],
            "broll": [],
        }

    prompt = PROMPT_TEMPLATE.format(
        niche_prompt=config.NICHE_PROMPTS[niche],
        domain=random.choice(config.NICHE_DOMAINS[niche]),
        hook_style=random.choice(config.HOOK_STYLES),
        banned=", ".join(f'"{{p}}"'.format(p=p) for p in config.BANNED_PHRASES),
        recent_topics=", ".join(recent_topics[-20:]) or "none",
    )
    text = _llm_text(prompt).strip()
    # Strip markdown fences if present
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    data = json.loads(text)
    for key in ("script", "title", "caption", "hashtags"):
        if key not in data:
            raise ValueError(f"LLM response missing '{key}'")

    # Second pass: rewrite the script to strip anything that sounds AI-written
    data["script"] = _humanize(data["script"])
    return data


HUMANIZE_PROMPT = """Below is a short-form video script. Rewrite it so it sounds \
like a real person talking off the top of their head - keep every fact, number \
and name exactly as is, keep it the same length, but fix anything that sounds \
scripted, formulaic, or AI-generated: remove cliches, vary the rhythm, make \
transitions feel spontaneous. If it already sounds natural, change very little.

Respond with ONLY the rewritten script text, nothing else.

SCRIPT:
{script}"""


def _humanize(script: str) -> str:
    try:
        out = _llm_text(HUMANIZE_PROMPT.format(script=script)).strip()
        out = re.sub(r'^["\']|["\']$', "", out).strip()
        # sanity: reject rewrites that lost too much content
        if len(out) > 0.6 * len(script):
            script = out
    except Exception as e:
        print(f"[humanize] skipped ({e})")
    for phrase in config.BANNED_PHRASES:
        if phrase in script.lower():
            print(f"[humanize] warning: banned phrase slipped through: {phrase}")
    return script
