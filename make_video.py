"""Turn a script into a finished 9:16 reel.

Steps: edge-tts voiceover (with word timings) -> Pexels background clip
(or animated gradient fallback) -> FFmpeg assembly with burned-in captions.
Only dependency beyond pip packages is ffmpeg.
"""
import asyncio
import json
import os
import random
import re
import subprocess
import tempfile

import requests

import config


# ---------------------------------------------------------------- TTS
async def _tts(script: str, voice: str, mp3_path: str, marks_path: str):
    import edge_tts

    communicate = edge_tts.Communicate(script, voice, rate="+8%")
    marks = []
    with open(mp3_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                marks.append(
                    {
                        "word": chunk["text"],
                        "start": chunk["offset"] / 10_000_000,
                        "end": (chunk["offset"] + chunk["duration"]) / 10_000_000,
                    }
                )
    with open(marks_path, "w") as f:
        json.dump(marks, f)


def synthesize(script: str, voice: str, workdir: str) -> tuple[str, list]:
    mp3 = os.path.join(workdir, "voice.mp3")
    marks_file = os.path.join(workdir, "marks.json")
    asyncio.run(_tts(script, voice, mp3, marks_file))
    with open(marks_file) as f:
        marks = json.load(f)
    return mp3, marks


def audio_duration(path: str) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", path]
    )
    return float(out.strip())


# ------------------------------------------------------- Background video
def fetch_background(niche: str, duration: float, workdir: str) -> str:
    """Download a portrait clip from Pexels; fall back to a generated gradient."""
    dest = os.path.join(workdir, "bg.mp4")
    if config.PEXELS_API_KEY:
        try:
            query = random.choice(config.NICHE_FOOTAGE[niche])
            r = requests.get(
                "https://api.pexels.com/videos/search",
                headers={"Authorization": config.PEXELS_API_KEY},
                params={"query": query, "orientation": "portrait", "per_page": 15},
                timeout=30,
            )
            r.raise_for_status()
            videos = r.json().get("videos", [])
            random.shuffle(videos)
            for v in videos:
                files = [
                    f for f in v.get("video_files", [])
                    if f.get("height", 0) >= 1280 and f.get("width", 0) < f.get("height", 0)
                ]
                if not files:
                    continue
                url = sorted(files, key=lambda f: f["height"])[0]["link"]
                with requests.get(url, stream=True, timeout=120) as resp:
                    resp.raise_for_status()
                    with open(dest, "wb") as fh:
                        for chunk in resp.iter_content(1 << 20):
                            fh.write(chunk)
                return dest
        except Exception as e:
            print(f"[bg] Pexels failed ({e}); using gradient fallback")

    # Fallback: animated dark gradient, always works offline
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi",
         "-i",
         f"gradients=size={config.VIDEO_W}x{config.VIDEO_H}:speed=0.03:"
         f"c0=0x0f0c29:c1=0x302b63:c2=0x24243e:nb_colors=3:duration={duration + 1}",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", dest],
        check=True, capture_output=True,
    )
    return dest


# ------------------------------------------------------------- Captions
def _ass_time(t: float) -> str:
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def build_captions(marks: list, workdir: str) -> str:
    """Word-grouped karaoke-style captions as an .ass subtitle file."""
    ass = os.path.join(workdir, "subs.ass")
    header = f"""[Script Info]
PlayResX: {config.VIDEO_W}
PlayResY: {config.VIDEO_H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Outline, Shadow, Alignment, MarginL, MarginR, MarginV
Style: Cap,Arial,88,&H00FFFFFF,&H00000000,&H80000000,-1,5,0,5,60,60,0

[Events]
Format: Layer, Start, End, Style, Text
"""
    lines = []
    group, gstart = [], None
    for i, mk in enumerate(marks):
        if gstart is None:
            gstart = mk["start"]
        group.append(mk["word"])
        end_of_group = len(group) >= 3 or i == len(marks) - 1
        if end_of_group:
            gend = mk["end"] + 0.05
            text = " ".join(group).upper()
            text = re.sub(r"[{}]", "", text)
            lines.append(f"Dialogue: 0,{_ass_time(gstart)},{_ass_time(gend)},Cap,{text}")
            group, gstart = [], None
    with open(ass, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(lines))
    return ass


# ------------------------------------------------------------- Assembly
def assemble(bg: str, voice: str, subs: str, duration: float, out_path: str):
    dur = min(duration + 0.4, config.MAX_DURATION)
    subs_escaped = subs.replace("\\", "/").replace(":", "\\:")
    vf = (
        f"scale={config.VIDEO_W}:{config.VIDEO_H}:force_original_aspect_ratio=increase,"
        f"crop={config.VIDEO_W}:{config.VIDEO_H},setsar=1,"
        f"eq=brightness=-0.08,ass='{subs_escaped}'"
    )
    subprocess.run(
        ["ffmpeg", "-y",
         "-stream_loop", "-1", "-i", bg,
         "-i", voice,
         "-t", f"{dur:.2f}",
         "-vf", vf,
         "-map", "0:v", "-map", "1:a",
         "-c:v", "libx264", "-preset", "fast", "-crf", "23",
         "-c:a", "aac", "-b:a", "128k",
         "-pix_fmt", "yuv420p", "-r", "30", "-shortest",
         out_path],
        check=True, capture_output=True,
    )


def make_reel(script: str, niche: str, out_path: str) -> str:
    with tempfile.TemporaryDirectory() as workdir:
        voice_file, marks = synthesize(script, config.NICHE_VOICES[niche], workdir)
        dur = audio_duration(voice_file)
        bg = fetch_background(niche, dur, workdir)
        subs = build_captions(marks, workdir)
        assemble(bg, voice_file, subs, dur, out_path)
    return out_path
