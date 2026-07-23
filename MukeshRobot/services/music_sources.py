"""Resolve queries / URLs to a streamable audio-or-video URL + metadata."""

import os
import re
import logging

import yt_dlp

LOGGER = logging.getLogger(__name__)

YT_RE = re.compile(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/", re.I)
SPOTIFY_RE = re.compile(r"(https?://)?(open\.)?spotify\.com/", re.I)

_AUDIO_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "default_search": "ytsearch",
}
_VIDEO_OPTS = {
    "format": "best[height<=720]/best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "default_search": "ytsearch",
}


def _extract(query: str, video: bool) -> dict | None:
    opts = _VIDEO_OPTS if video else _AUDIO_OPTS
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if "entries" in info:
                info = info["entries"][0]
            return {
                "title": info.get("title", query),
                "duration": info.get("duration", 0),
                "url": info["url"],
                "webpage_url": info.get("webpage_url"),
                "uploader": info.get("uploader"),
                "video": video,
            }
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("yt-dlp extraction failed: %s", exc)
        return None


def _resolve_spotify(spotify_url: str) -> str | None:
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not (client_id and client_secret):
        LOGGER.warning("Spotify credentials missing; cannot resolve Spotify URL.")
        return None
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(client_id, client_secret)
        )
        track = sp.track(spotify_url)
        title = track["name"]
        artists = ", ".join(a["name"] for a in track["artists"])
        return f"{title} {artists}"
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("Spotify resolution failed: %s", exc)
        return None


def resolve(query: str, video: bool = False) -> dict | None:
    if SPOTIFY_RE.search(query):
        search_str = _resolve_spotify(query)
        if not search_str:
            return None
        return _extract(f"ytsearch:{search_str}", video=video)
    if YT_RE.search(query):
        return _extract(query, video=video)
    return _extract(f"ytsearch:{query}", video=video)
