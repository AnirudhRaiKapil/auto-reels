# Reel Factory — 95%+ automated AI reels pipeline

Generates and publishes a faceless AI reel 4x/day to Instagram Reels and
YouTube Shorts. Runs free on GitHub Actions. Rotates 3 niches:
facts → motivation → AI/tech, one per run.

**Pipeline:** Gemini (script) → edge-tts (voiceover) → Pexels (background
footage) → FFmpeg (assembly + karaoke captions) → Graph API / YouTube API
(publish) → state committed back to repo (topic dedup).

## Setup (~45 min, one time)

### 1. Repo
Create a **private** GitHub repo, push this folder to it.

### 2. Free API keys
- **Gemini:** https://aistudio.google.com/apikey → create key (free tier)
- **Pexels:** https://www.pexels.com/api/ → create key (free)

### 3. Instagram
1. Convert your IG account to **Business/Creator** (app settings).
2. Link it to a Facebook Page.
3. Go to https://developers.facebook.com → create an app (type: Business).
4. Add the **Instagram Graph API** product.
5. In Graph API Explorer, generate a token with scopes:
   `instagram_basic, instagram_content_publish, pages_show_list, business_management`.
6. Exchange for a long-lived token (60 days):
   ```
   https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=APP_ID&client_secret=APP_SECRET&fb_exchange_token=SHORT_TOKEN
   ```
7. Get your IG user id:
   `GET /me/accounts` → page id → `GET /{page-id}?fields=instagram_business_account`
8. Note: token must be refreshed every ~60 days (5 min, the one manual chore).

### 4. YouTube
1. https://console.cloud.google.com → new project → enable **YouTube Data API v3**.
2. OAuth consent screen → External → add yourself as test user.
3. Credentials → OAuth client ID → **Desktop app** → download `client_secret.json`
   into the project root.
4. Locally run:
   ```
   pip install -r requirements.txt
   python scripts/youtube_auth.py
   ```
   This opens a browser and writes `token.json`.

### 5. GitHub secrets
Repo → Settings → Secrets and variables → Actions → add:

| Secret | Value |
|---|---|
| `GEMINI_API_KEY` | from step 2 |
| `PEXELS_API_KEY` | from step 2 |
| `IG_USER_ID` | from step 3 |
| `IG_ACCESS_TOKEN` | long-lived token from step 3 |
| `YT_TOKEN_JSON` | full contents of `token.json` |

### 6. Go live
Actions tab → "Publish reel" → **Run workflow** to test once.
Then the cron does 4 runs/day (9am, 2pm, 6pm, 10pm IST) automatically.

## Local testing
```
pip install -r requirements.txt          # needs ffmpeg installed too
python run.py --dry-run                  # makes a video, no publishing
python run.py --dry-run --niche facts    # force a niche
```
Works with zero keys (built-in fallback content + gradient background);
add GEMINI/PEXELS keys for real variety.

## Tuning
- Cadence: edit the cron in `.github/workflows/reel.yml`
- Niches, prompts, voices, footage themes: `config.py`
- Caption look: `build_captions()` style line in `make_video.py`

## Important notes
- **Don't raise cadence much above 4-6/day** — spam detection risk on both platforms.
- YouTube default quota = 6 uploads/day max; fits this cadence.
- New IG apps start in dev mode limits; request `instagram_content_publish`
  advanced access if publishing fails after ~25 posts.
- Disclose AI-generated content where required (YouTube has an AI-disclosure
  setting; some jurisdictions require labeling).
- The remaining 5% of manual work: refresh IG token every 60 days, glance at
  comments/analytics, occasionally prune weak topics from `config.py`.
