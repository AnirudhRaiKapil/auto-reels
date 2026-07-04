"""Central config for the reel factory."""
import os

# Niches rotate per run: run 1 -> facts, run 2 -> motivation, run 3 -> ai_news, ...
NICHES = ["facts", "motivation", "ai_news"]

NICHE_PROMPTS = {
    "facts": (
        "Write a script for a 40-45 second vertical video about ONE surprising, "
        "verifiable fact (science, history, geography, or the human body). "
        "Hook the viewer in the first sentence with a bold claim or question. "
        "Include at least three concrete specifics: real numbers, named places, "
        "people, or dates. Explain the WHY behind the fact, not just the what. "
        "End with one line that makes the viewer want to share it. "
        "100-125 words. Write like a person talking to a friend: contractions, "
        "short punchy sentences mixed with longer ones. No emojis, no hashtags."
    ),
    "motivation": (
        "Write a 40-45 second motivational monologue for a vertical video. "
        "Direct, second-person. One core idea (discipline, consistency, "
        "starting small, handling failure, etc.) explored with a concrete "
        "mini-story or vivid example the viewer can picture - a specific "
        "morning, a specific choice, a specific moment of wanting to quit. "
        "100-125 words. Contractions, natural rhythm, no cliches like "
        "'unleash your potential'. No emojis, no quotes from real people."
    ),
    "ai_news": (
        "Write a 40-45 second script explaining ONE interesting concept or "
        "development in AI/technology for a general audience. Hook first. "
        "Use one concrete analogy from everyday life, and at least two real "
        "specifics (numbers, company/product names, dates). Explain why it "
        "matters to the viewer personally by the end. 100-125 words. "
        "Conversational, contractions, no jargon without explaining it."
    ),
}

# Topic domains rotated randomly per run for variety
NICHE_DOMAINS = {
    "facts": ["the deep ocean", "space and astronomy", "ancient history",
              "the human body", "animal behavior", "physics in daily life",
              "geography extremes", "food history", "language and words",
              "weird laws and customs", "engineering marvels", "the brain and memory"],
    "motivation": ["discipline vs motivation", "starting before you're ready",
                   "handling failure", "comparison and envy", "consistency over intensity",
                   "doing hard things alone", "patience with slow progress",
                   "quitting bad habits", "fear of judgment", "tiny daily wins"],
    "ai_news": ["how AI models actually work", "AI in medicine", "AI and jobs",
                "robots and automation", "AI in your phone", "the cost of training AI",
                "AI mistakes and limits", "open source AI", "AI and creativity",
                "how recommendation algorithms shape you"],
}

# Hook styles rotated randomly so openings don't feel same-y
HOOK_STYLES = [
    "start with a startling specific number or statistic",
    "start with a short vivid scene, like the first line of a story",
    "start with a direct question to the viewer",
    "start with a confident claim most people would disagree with",
    "start mid-action, as if continuing a conversation",
]

# Phrases that make scripts sound AI-written. Never allow these.
BANNED_PHRASES = [
    "dive into", "delve", "game-changer", "here's the kicker", "let that sink in",
    "mind-blowing", "in today's world", "in this day and age", "buckle up",
    "get this", "believe it or not", "little did they know", "fun fact",
    "but wait", "plot twist", "the crazy part", "and the best part",
    "revolutionize", "unleash", "harness the power", "topic of", "world of",
]

# Voice per niche (edge-tts voices, all free)
NICHE_VOICES = {
    "facts": "en-US-AndrewMultilingualNeural",
    "motivation": "en-US-BrianMultilingualNeural",
    "ai_news": "en-US-EmmaMultilingualNeural",
}

# Pexels search terms per niche for background footage
NICHE_FOOTAGE = {
    "facts": ["space", "ocean", "nature aerial", "city timelapse", "science"],
    "motivation": ["gym workout", "sunrise", "running", "mountain climb", "city night"],
    "ai_news": ["technology", "server room", "circuit board", "futuristic", "coding"],
}

POSTS_PER_DAY = 5
# Hourly cron slots (UTC). 3-17 UTC = 8:30am-10:30pm IST posting window.
SLOT_HOURS_UTC = list(range(3, 18))

VIDEO_W, VIDEO_H = 1080, 1920  # 9:16
MAX_DURATION = 60              # seconds, Shorts/Reels safe

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
IG_USER_ID = os.getenv("IG_USER_ID", "")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")

OUT_DIR = os.path.join(os.path.dirname(__file__), "output")
STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")
