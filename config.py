"""Central config for the reel factory."""
import os

# Niches rotate per run: run 1 -> facts, run 2 -> motivation, run 3 -> ai_news, ...
NICHES = ["facts", "motivation", "ai_news"]

NICHE_PROMPTS = {
    "facts": (
        "Write a script for a 30-second vertical video about ONE surprising, "
        "verifiable fact (science, history, geography, or the human body). "
        "Hook the viewer in the first sentence. 60-80 words, spoken style, "
        "no emojis, no hashtags in the script."
    ),
    "motivation": (
        "Write a 30-second motivational monologue for a vertical video. "
        "Direct, second-person, punchy short sentences. One core idea "
        "(discipline, consistency, starting small, etc.). 60-80 words. "
        "No emojis, no quotes attributed to real people."
    ),
    "ai_news": (
        "Write a 30-second script explaining ONE interesting recent development "
        "or evergreen concept in AI/technology in simple terms for a general "
        "audience. Hook first, then explain why it matters. 60-80 words."
    ),
}

# Voice per niche (edge-tts voices, all free)
NICHE_VOICES = {
    "facts": "en-US-ChristopherNeural",
    "motivation": "en-US-GuyNeural",
    "ai_news": "en-US-AriaNeural",
}

# Pexels search terms per niche for background footage
NICHE_FOOTAGE = {
    "facts": ["space", "ocean", "nature aerial", "city timelapse", "science"],
    "motivation": ["gym workout", "sunrise", "running", "mountain climb", "city night"],
    "ai_news": ["technology", "server room", "circuit board", "futuristic", "coding"],
}

VIDEO_W, VIDEO_H = 1080, 1920  # 9:16
MAX_DURATION = 60              # seconds, Shorts/Reels safe

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
IG_USER_ID = os.getenv("IG_USER_ID", "")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")

OUT_DIR = os.path.join(os.path.dirname(__file__), "output")
STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")
