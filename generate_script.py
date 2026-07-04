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

PROMPT_TEMPLATE = """{niche_prompt}

Also avoid these recently used topics: {recent_topics}

Respond ONLY with JSON in this exact shape:
{{
  "script": "the spoken script",
  "title": "a click-worthy title under 90 characters",
  "caption": "an Instagram caption, 1-2 sentences",
  "hashtags": ["#tag1", "#tag2", "... 10 relevant hashtags"]
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
        }

    prompt = PROMPT_TEMPLATE.format(
        niche_prompt=config.NICHE_PROMPTS[niche],
        recent_topics=", ".join(recent_topics[-20:]) or "none",
    )
    text = _llm_text(prompt).strip()
    # Strip markdown fences if present
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    data = json.loads(text)
    for key in ("script", "title", "caption", "hashtags"):
        if key not in data:
            raise ValueError(f"Gemini response missing '{key}'")
    return data
