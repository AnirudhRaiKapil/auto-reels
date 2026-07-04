"""Fetch performance metrics for published reels and score niches."""
import datetime as dt
import random

import requests

import config


def _base() -> str:
    if config.IG_ACCESS_TOKEN.startswith("IGAA"):
        return "https://graph.instagram.com/v21.0"
    return "https://graph.facebook.com/v21.0"


def fetch_metrics(media_id: str) -> dict:
    """Views/likes/comments/shares/saves for one IG media object."""
    out = {}
    try:
        r = requests.get(
            f"{_base()}/{media_id}/insights",
            params={"metric": "views,likes,comments,shares,saved",
                    "access_token": config.IG_ACCESS_TOKEN},
            timeout=30,
        )
        if r.ok:
            for item in r.json().get("data", []):
                vals = item.get("values", [{}])
                out[item["name"]] = vals[0].get("value", 0) or 0
    except Exception as e:
        print(f"[analytics] insights failed for {media_id}: {e}")
    if not out:
        try:
            r = requests.get(
                f"{_base()}/{media_id}",
                params={"fields": "like_count,comments_count",
                        "access_token": config.IG_ACCESS_TOKEN},
                timeout=30,
            )
            if r.ok:
                d = r.json()
                out = {"likes": d.get("like_count", 0),
                       "comments": d.get("comments_count", 0)}
        except Exception as e:
            print(f"[analytics] fallback failed for {media_id}: {e}")
    return out


def refresh(state: dict, max_items: int = 15):
    """Update metrics on recent published posts (only ones older than 1h)."""
    if not config.IG_ACCESS_TOKEN:
        return
    now = dt.datetime.utcnow()
    updated = 0
    for h in state.get("history", [])[-max_items:]:
        mid = h.get("instagram")
        if not mid:
            continue
        try:
            age_h = (now - dt.datetime.strptime(h["time"], "%Y%m%d_%H%M%S")).total_seconds() / 3600
        except ValueError:
            continue
        if age_h < 1:
            continue
        m = fetch_metrics(mid)
        if m:
            h["metrics"] = m
            h["metrics_at"] = now.strftime("%Y%m%d_%H%M%S")
            updated += 1
    if updated:
        print(f"[analytics] refreshed metrics on {updated} posts")


def _score(h: dict) -> float:
    m = h.get("metrics", {})
    # views dominate; engagement actions weighted heavier per unit
    return (m.get("views", 0) + 5 * m.get("likes", 0) + 20 * m.get("shares", 0)
            + 20 * m.get("saved", 0) + 10 * m.get("comments", 0))


def pick_niche(state: dict, rotation_index: int) -> str:
    """Performance-weighted niche choice with 30% exploration.

    Falls back to plain rotation until every niche has >= 2 scored posts.
    """
    scored = {n: [] for n in config.NICHES}
    for h in state.get("history", []):
        if h.get("niche") in scored and "metrics" in h:
            scored[h["niche"]].append(_score(h))

    if any(len(v) < 2 for v in scored.values()):
        return config.NICHES[rotation_index % len(config.NICHES)]

    if random.random() < 0.30:  # exploration
        return random.choice(config.NICHES)

    avgs = {n: sum(v[-10:]) / len(v[-10:]) for n, v in scored.items()}
    best = max(avgs, key=avgs.get)
    print(f"[analytics] niche scores: {avgs} -> {best}")
    return best
