"""Publish a finished reel to Instagram (Graph API) and YouTube (Data API)."""
import os
import time

import requests

import config

def _graph_base():
    """Instagram Login tokens (IGAA...) use graph.instagram.com;
    Facebook Login tokens (EAA...) use graph.facebook.com."""
    import config as _c
    if _c.IG_ACCESS_TOKEN.startswith("IGAA"):
        return "https://graph.instagram.com/v21.0"
    return "https://graph.facebook.com/v21.0"

GRAPH = _graph_base()


# ------------------------------------------------------------ File host
def _host_github_release(path: str) -> str:
    """Upload the video as a release asset on this repo (public, free, reliable)."""
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    api = f"https://api.github.com/repos/{repo}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

    tag = "media-" + time.strftime("%Y%m%d-%H%M%S")
    r = requests.post(f"{api}/releases", headers=headers,
                      json={"tag_name": tag, "name": tag, "prerelease": True}, timeout=60)
    r.raise_for_status()
    rel = r.json()
    upload_url = rel["upload_url"].split("{")[0]
    with open(path, "rb") as f:
        r = requests.post(
            f"{upload_url}?name=reel.mp4",
            headers={**headers, "Content-Type": "video/mp4"},
            data=f, timeout=600,
        )
    r.raise_for_status()
    url = r.json()["browser_download_url"]

    # Housekeeping: keep only the 12 newest media releases
    try:
        rels = requests.get(f"{api}/releases?per_page=100", headers=headers, timeout=60).json()
        media = [x for x in rels if x["tag_name"].startswith("media-")]
        for old in media[12:]:
            requests.delete(f"{api}/releases/{old['id']}", headers=headers, timeout=30)
            requests.delete(f"{api}/git/refs/tags/{old['tag_name']}", headers=headers, timeout=30)
    except Exception:
        pass
    return url


def _host_tmpfiles(path: str) -> str:
    with open(path, "rb") as f:
        r = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=300)
    r.raise_for_status()
    url = r.json()["data"]["url"]
    return url.replace("tmpfiles.org/", "tmpfiles.org/dl/")


def host_video(path: str) -> str:
    """Instagram's API requires a public video URL. Tries GitHub release
    assets first (works from Actions), then tmpfiles.org."""
    errors = []
    if os.getenv("GITHUB_TOKEN") and os.getenv("GITHUB_REPOSITORY"):
        try:
            return _host_github_release(path)
        except Exception as e:
            errors.append(f"github: {e}")
    try:
        return _host_tmpfiles(path)
    except Exception as e:
        errors.append(f"tmpfiles: {e}")
    raise RuntimeError("all video hosts failed: " + "; ".join(errors))


# ------------------------------------------------------------ Instagram
def publish_instagram(video_url: str, caption: str) -> str:
    r = requests.post(
        f"{GRAPH}/{config.IG_USER_ID}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": config.IG_ACCESS_TOKEN,
        },
        timeout=60,
    )
    r.raise_for_status()
    container_id = r.json()["id"]

    # Wait for Instagram to process the container
    for _ in range(40):
        s = requests.get(
            f"{GRAPH}/{container_id}",
            params={"fields": "status_code", "access_token": config.IG_ACCESS_TOKEN},
            timeout=30,
        ).json()
        code = s.get("status_code")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise RuntimeError(f"IG processing error: {s}")
        time.sleep(15)
    else:
        raise TimeoutError("IG container never finished processing")

    r = requests.post(
        f"{GRAPH}/{config.IG_USER_ID}/media_publish",
        data={"creation_id": container_id, "access_token": config.IG_ACCESS_TOKEN},
        timeout=60,
    )
    r.raise_for_status()
    media_id = r.json()["id"]
    print(f"[instagram] published media {media_id}")
    return media_id


# ------------------------------------------------------------- Facebook
def publish_facebook(video_url: str, description: str) -> str:
    """Post the reel video to a Facebook Page."""
    r = requests.post(
        f"https://graph.facebook.com/v21.0/{config.FB_PAGE_ID}/videos",
        data={
            "file_url": video_url,
            "description": description,
            "access_token": config.FB_PAGE_TOKEN,
        },
        timeout=300,
    )
    r.raise_for_status()
    vid = r.json()["id"]
    print(f"[facebook] published video {vid}")
    return vid


# ------------------------------------------------------------- YouTube
def publish_youtube(video_path: str, title: str, description: str, tags: list) -> str:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    token_file = os.path.join(os.path.dirname(__file__), "token.json")
    creds = Credentials.from_authorized_user_file(
        token_file, ["https://www.googleapis.com/auth/youtube.upload"]
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    yt = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {
            "title": title[:100],
            "description": f"{description}\n\n#Shorts",
            "tags": [t.lstrip("#") for t in tags][:15],
            "categoryId": "27",  # Education
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    print(f"[youtube] published video {resp['id']}")
    return resp["id"]
