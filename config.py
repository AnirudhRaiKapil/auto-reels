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

VIDEO_W, VIDEO_H = 1080, 1920  # 9:16
MAX_DURATION = 60              # seconds, Shorts/Reels safe

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
IG_USER_ID = os.getenv("IG_USER_ID", "")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")

OUT_DIR = os.path.join(os.path.dirname(__file__), "output")
STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")
