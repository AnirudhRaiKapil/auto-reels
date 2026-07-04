"""One full pipeline run: pick niche -> script -> video -> publish everywhere.

Usage:
  python run.py                 # generate + publish
  python run.py --dry-run       # generate video only, skip publishing
"""
import argparse
import datetime
import json
import os
import sys

import config
import generate_script
import make_video


def load_state() -> dict:
    if os.path.exists(config.STATE_FILE):
        with open(config.STATE_FILE) as f:
            return json.load(f)
    return {"run_count": 0, "recent_topics": [], "history": []}


def save_state(state: dict):
    with open(config.STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--niche", choices=config.NICHES)
    args = parser.parse_args()

    state = load_state()
    niche = args.niche or config.NICHES[state["run_count"] % len(config.NICHES)]
    print(f"[run] #{state['run_count'] + 1} niche={niche}")

    content = generate_script.generate(niche, state["recent_topics"])
    print(f"[run] title: {content['title']}")

    os.makedirs(config.OUT_DIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(config.OUT_DIR, f"reel_{niche}_{stamp}.mp4")
    make_video.make_reel(content["script"], niche, out_path)
    size_mb = os.path.getsize(out_path) / 1e6
    print(f"[run] video ready: {out_path} ({size_mb:.1f} MB)")

    results = {"video": out_path, "title": content["title"]}
    if not args.dry_run:
        import publish

        caption = content["caption"] + "\n\n" + " ".join(content["hashtags"])
        errors = []
        if config.IG_USER_ID and config.IG_ACCESS_TOKEN:
            try:
                results["instagram"] = publish.publish_instagram(out_path, caption)
            except Exception as e:
                errors.append(f"instagram: {e}")
        if os.path.exists(os.path.join(os.path.dirname(__file__), "token.json")):
            try:
                results["youtube"] = publish.publish_youtube(
                    out_path, content["title"], content["caption"], content["hashtags"]
                )
            except Exception as e:
                errors.append(f"youtube: {e}")
        for err in errors:
            print(f"[run] PUBLISH FAILED -> {err}", file=sys.stderr)

    state["run_count"] += 1
    state["recent_topics"].append(content["title"])
    state["recent_topics"] = state["recent_topics"][-50:]
    state["history"].append({"time": stamp, "niche": niche, **{k: v for k, v in results.items() if k != "video"}})
    state["history"] = state["history"][-200:]
    save_state(state)
    print("[run] done")


if __name__ == "__main__":
    main()
