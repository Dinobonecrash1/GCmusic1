"""
Music/Video streaming client — Pyrogram userbot + PyTgCalls.

Runs a background asyncio loop in a dedicated thread so the synchronous
python-telegram-bot 13.15 handlers can drive it via `run_coroutine_threadsafe`.
Also handles auto-advance via PyTgCalls `StreamEnded` update.
"""

import asyncio
import logging
import os
import threading
from typing import Callable, Optional

from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
from pytgcalls.types.stream import StreamAudioEnded, StreamVideoEnded

LOGGER = logging.getLogger(__name__)

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
STRING_SESSION = os.environ.get("STRING_SESSION", "")


class MusicClient:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.loop = asyncio.new_event_loop()
        # chat_id -> list[dict(title, url, video, requested_by, webpage_url)]
        self.queues: dict[int, list[dict]] = {}
        # chat_id -> currently playing dict
        self.current: dict[int, dict] = {}
        # optional callback(chat_id, next_item_or_None) fired on auto-advance
        self.on_advance: Optional[Callable[[int, Optional[dict]], None]] = None

        if not (API_ID and API_HASH and STRING_SESSION):
            LOGGER.warning("Music disabled: API_ID / API_HASH / STRING_SESSION not set.")
            self.enabled = False
            self.app = None
            self.calls = None
            return

        self.enabled = True
        self.app = Client(
            name="assistant",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=STRING_SESSION,
        )
        self.calls = PyTgCalls(self.app)
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        asyncio.run_coroutine_threadsafe(self._start(), self.loop)

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def _start(self):
        try:
            await self.app.start()
            await self.calls.start()

            @self.calls.on_update(StreamAudioEnded())
            async def _audio_ended(_, update):
                await self._advance(update.chat_id)

            @self.calls.on_update(StreamVideoEnded())
            async def _video_ended(_, update):
                await self._advance(update.chat_id)

            LOGGER.info("MusicClient started successfully.")
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Failed to start MusicClient: %s", exc)

    async def _advance(self, chat_id: int):
        """Called when a stream ends — play next queued item or leave the call."""
        q = self.queues.get(chat_id, [])
        if q:
            q.pop(0)
        nxt = q[0] if q else None
        try:
            if nxt:
                await self._play_stream(chat_id, nxt)
                self.current[chat_id] = nxt
            else:
                self.current.pop(chat_id, None)
                await self.calls.leave_call(chat_id)
                self.queues.pop(chat_id, None)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("auto-advance failed: %s", exc)
        finally:
            if self.on_advance:
                try:
                    self.on_advance(chat_id, nxt)
                except Exception:  # noqa: BLE001
                    LOGGER.exception("on_advance callback errored")

    async def _play_stream(self, chat_id: int, item: dict):
        if item.get("video"):
            stream = MediaStream(
                item["url"],
                audio_flags=MediaStream.Flags.REQUIRED,
                video_flags=MediaStream.Flags.REQUIRED,
                audio_parameters=AudioQuality.STUDIO,
                video_parameters=VideoQuality.HD_720p,
            )
        else:
            stream = MediaStream(item["url"], audio_flags=MediaStream.Flags.REQUIRED)
        await self.calls.play(chat_id, stream)

    # -------- sync wrappers --------
    def _run(self, coro):
        if not self.enabled:
            raise RuntimeError("Music engine is disabled (missing env vars).")
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout=60)

    def play(self, chat_id: int, item: dict):
        self.current[chat_id] = item
        return self._run(self._play_stream(chat_id, item))

    def pause(self, chat_id: int):
        return self._run(self.calls.pause(chat_id))

    def resume(self, chat_id: int):
        return self._run(self.calls.resume(chat_id))

    def stop(self, chat_id: int):
        self.queues.pop(chat_id, None)
        self.current.pop(chat_id, None)
        return self._run(self.calls.leave_call(chat_id))

    def skip(self, chat_id: int) -> Optional[dict]:
        """Advance to the next queued item. Returns the new 'current' or None."""
        q = self.queues.get(chat_id, [])
        if q:
            q.pop(0)
        nxt = q[0] if q else None
        if nxt:
            self.current[chat_id] = nxt
            self._run(self._play_stream(chat_id, nxt))
        else:
            self.current.pop(chat_id, None)
            try:
                self._run(self.calls.leave_call(chat_id))
            except Exception:  # noqa: BLE001
                pass
            self.queues.pop(chat_id, None)
        return nxt

    # -------- queue helpers --------
    def enqueue(self, chat_id: int, item: dict) -> int:
        self.queues.setdefault(chat_id, []).append(item)
        return len(self.queues[chat_id])

    def get_queue(self, chat_id: int) -> list[dict]:
        return list(self.queues.get(chat_id, []))

    def get_current(self, chat_id: int) -> Optional[dict]:
        return self.current.get(chat_id)
