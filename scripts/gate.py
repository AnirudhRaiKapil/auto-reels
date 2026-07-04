"""Decide whether this hourly run should post, so that POSTS_PER_DAY posts
land at random hours each day. Writes post=true/false to GITHUB_OUTPUT."""
import datetime as dt
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import config  # noqa: E402

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def posts_today() -> int:
    if not os.path.exists(config.STATE_FILE):
        return 0
    with open(config.STATE_FILE) as f:
        state = json.load(f)
    today = dt.datetime.now(dt.timezone.utc).astimezone(IST).date()
    n = 0
    for h in state.get("history", []):
        try:
            t = dt.datetime.strptime(h["time"], "%Y%m%d_%H%M%S")
            t = t.replace(tzinfo=dt.timezone.utc).astimezone(IST)
            if t.date() == today:
                n += 1
        except (ValueError, KeyError):
            pass
    return n


def decide() -> bool:
    if os.getenv("FORCE_POST") == "1":
        return True
    needed = config.POSTS_PER_DAY - posts_today()
    if needed <= 0:
        return False
    now_h = dt.datetime.now(dt.timezone.utc).hour
    remaining = len([h for h in config.SLOT_HOURS_UTC if h >= now_h])
    if remaining <= needed:
        return True  # running out of slots today, must post
    return random.random() < needed / remaining


if __name__ == "__main__":
    post = decide()
    print(f"[gate] posts today so far + decision: post={post}")
    out = os.getenv("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"post={'true' if post else 'false'}\n")
