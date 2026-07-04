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
    """Call Claude if ANTHROPIC_API_KEY is set, otherwise Gemini."""
    if config.ANTHROPIC_API_KEY:
        import anthropic

        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text

    from google import genai

    # Supports both key types: AIzaSy... (AI Studio) and AQ.... (Vertex express)
    if config.GEMINI_API_KEY.startswith("AQ."):
        client = genai.Client(vertexai=True, api_key=config.GEMINI_API_KEY)
    else:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
    resp = client.models.generate_content(model=config.GEMINI_MODEL, contents=prompt)
    return resp.text


def generate(niche: str, recent_topics: list[str]) -> dict:
    if not (config.GEMINI_API_KEY or config.ANTHROPIC_API_KEY):
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
