"""One-time YouTube OAuth. Run locally: python scripts/youtube_auth.py
Requires client_secret.json (OAuth Desktop credentials) in project root.
Produces token.json — paste its contents into the YT_TOKEN_JSON GitHub secret."""
import os
from google_auth_oauthlib.flow import InstalledAppFlow

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
flow = InstalledAppFlow.from_client_secrets_file(
    os.path.join(ROOT, "client_secret.json"),
    ["https://www.googleapis.com/auth/youtube.upload"],
)
creds = flow.run_local_server(port=0)
with open(os.path.join(ROOT, "token.json"), "w") as f:
    f.write(creds.to_json())
print("token.json written. Add its contents as the YT_TOKEN_JSON GitHub secret.")
