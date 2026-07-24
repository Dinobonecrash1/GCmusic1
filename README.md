<p align="center">
  <h1 align="center">GCmusic1</h1>
  <p align="center">A feature-rich Telegram bot with music streaming, group management, chatbot, anime info, and more.</p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-GPL--3.0-green" alt="License GPL-3.0">
  <img src="https://img.shields.io/badge/telegram-bot-blue?logo=telegram" alt="Telegram Bot">
  <img src="https://img.shields.io/badge/pytgcalls-v4-orange" alt="PyTgCalls v4">
</p>

---

## Features

### 🎵 Music & Video Streaming
Stream audio/video in Telegram voice chats via PyTgCalls v4.

| Command | Description |
|---------|-------------|
| `/play <query/url>` | Play audio in voice chat |
| `/vplay <query/url>` | Play video in voice chat |
| `/pause` | Pause playback |
| `/resume` | Resume playback |
| `/skip` | Skip to next track |
| `/stop` | Stop playback and leave VC |
| `/queue` | Show current queue |
| `/player` | Show now-playing panel |
| `/topsongs` | Show trending songs |
| `/song <query>` | Download song as audio file |

### 👮 Group Administration
Ban, kick, mute, warn, locks, notes, rules, filters, antiflood, welcome messages, blacklist, and more.

### 🤖 Chatbot
AI-powered conversational chatbot. Toggle with `/chatbot` (admin only). Configure via `CHATBOT_API_URL`.

### 🎌 Anime & Manga
- `/anime <name>` — anime info from AniList
- `/manga <name>` — manga info
- `/character <name>` — character lookup
- `/user <MAL username>` — MyAnimeList profile
- `/upcoming` — upcoming anime list
- `/airing <name>` — airing schedule

### 🎲 Extras
Fun commands, AI image generation, weather, Wikipedia, URL shortener, currency converter, translation, and more.

---

## Requirements

- **Python** 3.10+
- **MongoDB** (required for bot data)
- **PostgreSQL** (optional, for group management SQL features)
- **Telegram API credentials** (API_ID, API_HASH from [my.telegram.org](https://my.telegram.org))
- **Bot token** from [@BotFather](https://t.me/BotFather)
- **Pyrogram v2 string session** (for userbot music streaming)

---

## Setup & Installation

```bash
# 1. Clone the repository
git clone https://github.com/Dinobonecrash1/GCmusic1.git
cd GCmusic1

# 2. Create your environment file
cp .env.example .env

# 3. Edit .env and fill in your credentials
nano .env

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the bot
python -m MukeshRobot
```

### Generating a String Session

```bash
pip install "pyrogram==2.0.106" "tgcrypto==1.2.5"
python -c "from pyrogram import Client; \
           Client('gen', api_id=YOUR_API_ID, api_hash='YOUR_API_HASH').run(lambda: None)"
```
Then use `Client.export_session_string()` from an interactive shell.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TOKEN` | ✅ | Telegram bot token from BotFather |
| `API_ID` | ✅ | Telegram API ID from my.telegram.org |
| `API_HASH` | ✅ | Telegram API hash from my.telegram.org |
| `STRING_SESSION` | ✅ | Pyrogram v2 string session for the assistant userbot |
| `MONGO_DB_URI` | ✅ | MongoDB connection URI |
| `DATABASE_URL` | ❌ | PostgreSQL URL (for SQL-based features) |
| `OWNER_ID` | ✅ | Your Telegram user ID |
| `SUPPORT_CHAT` | ❌ | Support group username (without @) |
| `EVENT_LOGS` | ❌ | Chat ID for event logging |
| `START_IMG` | ❌ | Image URL shown on /start |
| `SPOTIFY_CLIENT_ID` | ❌ | Spotify app client ID (for link resolution) |
| `SPOTIFY_CLIENT_SECRET` | ❌ | Spotify app client secret |
| `CASH_API_KEY` | ❌ | API key for currency conversion |
| `TIME_API_KEY` | ❌ | API key for timezone lookups |
| `CHATBOT_API_URL` | ❌ | Custom chatbot API endpoint URL |
| `ENV` | ❌ | Set to `True` for production |
| `ALLOW_EXCL` | ❌ | Allow `!` as command prefix (default: True) |
| `DEL_CMDS` | ❌ | Delete command messages after execution |
| `STRICT_GBAN` | ❌ | Enforce global bans strictly |
| `WORKERS` | ❌ | Number of worker threads (default: 8) |

---

## Deployment

### VPS / Local Server
Follow the setup instructions above. Use `screen`, `tmux`, or a systemd service to keep the bot running.

```bash
# Example with screen
screen -S gcmusic
python -m MukeshRobot
# Detach: Ctrl+A, D
```

### Heroku
1. Fork this repository.
2. Create a new Heroku app.
3. Set all required environment variables in the Heroku dashboard (Settings → Config Vars).
4. Connect your GitHub fork and deploy.

> **Note**: Heroku's free tier has been discontinued. A paid plan is required.

---

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'feat: add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).

---

<p align="center">
  Made with ❤️ for the Telegram community
</p>
