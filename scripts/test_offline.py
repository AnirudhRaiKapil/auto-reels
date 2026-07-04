"""Offline smoke test: validates captions + ffmpeg assembly with mock TTS."""
import os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import make_video, config

script = "Your bones are constantly being replaced every ten years"
words = script.split()
dur = 8.0
per = dur / len(words)
marks = [{"word": w, "start": i * per, "end": (i + 1) * per} for i, w in enumerate(words)]

with tempfile.TemporaryDirectory() as wd:
    voice = os.path.join(wd, "voice.mp3")
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency=220:duration={dur}",
                    "-c:a", "libmp3lame", voice], check=True, capture_output=True)
    bg = make_video.fetch_background("facts", dur, wd)
    subs = make_video.build_captions(marks, wd)
    out = "/sessions/cool-youthful-turing/mnt/outputs/reel-factory/output/test_reel.mp4"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    make_video.assemble(bg, voice, subs, dur, out)
    probe = subprocess.check_output(
        ["ffprobe", "-v", "quiet", "-show_entries", "stream=width,height,codec_name",
         "-show_entries", "format=duration", "-of", "csv", out]).decode()
    print(probe)
    print(f"OK: {os.path.getsize(out)/1e6:.1f} MB")
