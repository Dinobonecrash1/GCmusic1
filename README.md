# LadyRezebb — Group Management + Music Bot

Telegram group management bot (based on MukeshRobot) with a **music module for
voice chats** powered by [PyTgCalls](https://github.com/pytgcalls/pytgcalls).

## What's inside

* Full group management (bans, mutes, filters, notes, welcome, warns, feds, AFK, ...).
* AI, anime, utility, and fun modules.
* **NEW: Music + Video module** for Telegram group **voice chats**:
  * `/play` — stream audio from a YouTube link, Spotify link, or search query.
  * `/vplay` — stream **video** (up to 720p) into the voice chat.
  * `/pause`, `/resume`, `/skip`, `/stop`/`/end`, `/queue` — playback controls (admin-only).
  * `/player` — interactive control panel with inline buttons (Pause / Resume / Skip / Stop / Queue).
  * `/topsongs` — top 10 most-requested tracks per group (MongoDB-backed leaderboard).
  * **Auto-advance** — when a stream ends, the next track in the queue starts automatically.
* YouTube (yt-dlp) and Spotify (resolved via YouTube) as sources.

## Fixes applied

* `MukeshRobot/__main__.py` — added the missing `html`, `json`, `traceback` imports (previously crashed inside `error_handler`).
* `requirements.txt` — removed broken `asyncio==3.4.3` pin (which is stdlib now and breaks on Python 3.11), relaxed `lxml` pin, added music dependencies (`py-tgcalls`, `yt-dlp`, `spotipy`).
* Refreshed `Dockerfile` for Python 3.11 + FFmpeg + libopus.

## Deployment

### 1. Environment variables

Copy `.env.example` → `.env` and fill in the values:

| Variable          | How to obtain                                                                 |
| ----------------- | ----------------------------------------------------------------------------- |
| `TOKEN`           | Chat with [@BotFather](https://t.me/BotFather) → `/newbot`                    |
| `API_ID`/`API_HASH` | https://my.telegram.org → API development tools                            |
| `STRING_SESSION` | Pyrogram v2 string session of your **assistant** userbot (a real Telegram account, **not the bot**). See helper below. |
| `MONGO_DB_URI`   | https://mongodb.com/atlas — free tier is fine                                 |
| `DATABASE_URL`   | Postgres URL (Heroku Postgres / Neon / Railway Postgres)                       |
| `OWNER_ID`       | Your Telegram numeric user ID (send `/id` to [@MissRose_bot](https://t.me/MissRose_bot)) |
| `SUPPORT_CHAT`   | Username of your support group (no `@`)                                        |
| `EVENT_LOGS`     | Numeric ID of a channel where the bot posts important events                   |
| `START_IMG`      | Telegraph URL of the picture shown on `/start`                                 |

### 2. Generate the Pyrogram STRING_SESSION (assistant userbot)

On your local machine (not the deployment server):

```bash
pip install "pyrogram==2.0.106" "tgcrypto==1.2.5"
python - <<'PY'
from pyrogram import Client
api_id  = int(input("API_ID: "))
api_hash = input("API_HASH: ").strip()
with Client("gen", api_id=api_id, api_hash=api_hash, in_memory=True) as app:
    print("\n\nSTRING_SESSION =", app.export_session_string())
PY
```

Paste the printed value into `.env` as `STRING_SESSION`. **This is the account
that will actually join voice chats — add it to your groups and promote it with
"Manage Voice Chats" permission.**

### 3. Deploy

**Docker (recommended for VPS / Koyeb / Railway):**

```bash
docker build -t ladyrezebb .
docker run --env-file .env --restart unless-stopped ladyrezebb
```

**Heroku (needs the FFmpeg buildpack in addition to Python):**

```bash
heroku create your-app
heroku buildpacks:add https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest
heroku buildpacks:add heroku/python
heroku config:set $(cat .env | xargs)
git push heroku main
heroku ps:scale worker=1
```

**Local:**

```bash
apt-get install -y ffmpeg
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)
python3 -m MukeshRobot
```

## Music & video usage

1. Add the **bot** (your `TOKEN` account) to the group — it handles commands.
2. Add the **assistant userbot** (your `STRING_SESSION` account) to the same group and promote it with *Manage Voice Chats*.
3. Start a voice chat in the group.
4. Send `/play <query or YouTube/Spotify link>` for audio, or `/vplay <...>` for video (up to 720p).
5. Control with `/pause`, `/resume`, `/skip`, `/stop`, `/queue`, or open the interactive panel with `/player`.
6. See the group's most-played tracks with `/topsongs`.
7. When a track ends, the next one in the queue plays automatically — no need to `/skip` manually.

## Notes

* The music module fails softly if `API_ID` / `API_HASH` / `STRING_SESSION` are not set — the rest of the bot still works.
* Spotify link resolution requires `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` (from https://developer.spotify.com/dashboard). Without them, Spotify links won't be resolved (search queries and YouTube links keep working).
* FFmpeg + libopus must be installed on the host (already handled in the Dockerfile).
