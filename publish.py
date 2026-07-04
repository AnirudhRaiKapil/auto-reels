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
def host_video(path: str) -> str:
    """Instagram's API requires a public video URL. Uses catbox.moe (free).
    Swap for S3/R2/your own host if you outgrow it."""
    with open(path, "rb") as f:
        r = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": f},
            timeout=300,
        )
    r.raise_for_status()
    url = r.text.strip()
    if not url.startswith("http"):
        raise RuntimeError(f"catbox upload failed: {url}")
    return url


# ------------------------------------------------------------ Instagram
def publish_instagram(video_path: str, caption: str) -> str:
    video_url = host_video(video_path)
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
