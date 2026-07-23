"""
Music + Video voice-chat commands.

Commands
--------
/play, /vplay   Play audio (or video) in the group's voice chat.
/pause /resume  Pause/resume current stream.
/skip           Skip to the next track (auto-advance is also wired to StreamEnded).
/stop /end      Stop playback and clear queue.
/queue          Show current queue.
/player         Interactive control panel (buttons).
/topsongs       Top 10 most-requested tracks in the current chat (MongoDB-backed).
"""

import logging
from datetime import datetime, timezone

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    Update,
)
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from MukeshRobot import MONGO_DB_URI, dispatcher
from MukeshRobot.modules.helper_funcs.chat_status import user_admin, is_user_admin
from MukeshRobot.services.music_client import MusicClient
from MukeshRobot.services.music_sources import resolve

LOGGER = logging.getLogger(__name__)

__mod_name__ = "Music"

__help__ = """
❍ /play <query|YouTube|Spotify> — play audio in the voice chat.
❍ /vplay <query|YouTube|Spotify> — play *video* in the voice chat.
❍ /pause — pause the current stream.
❍ /resume — resume the paused stream.
❍ /skip — skip to the next track in the queue.
❍ /stop or /end — stop playback and clear the queue.
❍ /queue — show the queue.
❍ /player — interactive control panel with buttons.
❍ /topsongs — top 10 most-requested tracks in this group.

Setup: add the *assistant userbot* (STRING_SESSION account) to the group and
promote it with "Manage Voice Chats", then start a voice chat.
"""

# ---------- leaderboard (sync pymongo, optional) ----------
try:
    from pymongo import MongoClient
    _mongo = MongoClient(MONGO_DB_URI) if MONGO_DB_URI else None
    _topsongs = _mongo.get_default_database()["music_topsongs"] if _mongo else None
except Exception as exc:  # noqa: BLE001
    LOGGER.warning("Leaderboard disabled — MongoDB unavailable: %s", exc)
    _topsongs = None


def _log_play(chat_id: int, item: dict):
    if _topsongs is None:
        return
    try:
        _topsongs.update_one(
            {"chat_id": chat_id, "title": item["title"]},
            {
                "$inc": {"plays": 1},
                "$set": {
                    "webpage_url": item.get("webpage_url"),
                    "last_played": datetime.now(timezone.utc),
                },
            },
            upsert=True,
        )
    except Exception:  # noqa: BLE001
        LOGGER.exception("failed to log play for topsongs")


# ---------- helpers ----------
def _mc() -> MusicClient:
    return MusicClient()


def _player_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏸ Pause", callback_data="mus_pause"),
                InlineKeyboardButton("▶️ Resume", callback_data="mus_resume"),
            ],
            [
                InlineKeyboardButton("⏭ Skip", callback_data="mus_skip"),
                InlineKeyboardButton("⏹ Stop", callback_data="mus_stop"),
            ],
            [InlineKeyboardButton("📋 Queue", callback_data="mus_queue")],
        ]
    )


def _now_playing_text(item: dict) -> str:
    kind = "📹 Video" if item.get("video") else "🎵 Audio"
    return (
        f"*{kind} — Now playing*\n"
        f"`{item['title']}`\n\n"
        f"Requested by: {item['requested_by']}"
    )


# ---------- /play + /vplay ----------
def _play_impl(update: Update, context: CallbackContext, video: bool):
    msg = update.effective_message
    chat = update.effective_chat
    if chat.type == "private":
        msg.reply_text("❍ Use this command inside a group with an active voice chat.")
        return
    if not context.args:
        cmd = "/vplay" if video else "/play"
        msg.reply_text(f"❍ Usage: {cmd} <song name | YouTube link | Spotify link>")
        return

    query = " ".join(context.args)
    status = msg.reply_text(f"🔍 Searching: `{query}` ...", parse_mode=ParseMode.MARKDOWN)

    track = resolve(query, video=video)
    if not track:
        status.edit_text("❌ Couldn't find anything for that query.")
        return

    mc = _mc()
    if not mc.enabled:
        status.edit_text(
            "❌ Music engine disabled. Set `API_ID`, `API_HASH`, `STRING_SESSION` env vars.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    item = {
        "title": track["title"],
        "url": track["url"],
        "webpage_url": track.get("webpage_url"),
        "video": video,
        "requested_by": update.effective_user.first_name,
    }

    if mc.get_current(chat.id):
        pos = mc.enqueue(chat.id, item)
        status.edit_text(
            f"➕ Added to queue at position `{pos}`:\n`{item['title']}`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    try:
        mc.enqueue(chat.id, item)
        mc.play(chat.id, item)
        _log_play(chat.id, item)
        status.edit_text(
            _now_playing_text(item),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_player_kb(),
        )
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("play failed: %s", exc)
        status.edit_text(f"❌ Failed to start playback: `{exc}`", parse_mode=ParseMode.MARKDOWN)


def play_cmd(update: Update, context: CallbackContext):
    _play_impl(update, context, video=False)


def vplay_cmd(update: Update, context: CallbackContext):
    _play_impl(update, context, video=True)


# ---------- control commands ----------
@user_admin
def pause_cmd(update: Update, context: CallbackContext):
    try:
        _mc().pause(update.effective_chat.id)
        update.effective_message.reply_text("⏸ Paused.")
    except Exception as exc:  # noqa: BLE001
        update.effective_message.reply_text(f"❌ Pause failed: `{exc}`", parse_mode=ParseMode.MARKDOWN)


@user_admin
def resume_cmd(update: Update, context: CallbackContext):
    try:
        _mc().resume(update.effective_chat.id)
        update.effective_message.reply_text("▶️ Resumed.")
    except Exception as exc:  # noqa: BLE001
        update.effective_message.reply_text(f"❌ Resume failed: `{exc}`", parse_mode=ParseMode.MARKDOWN)


@user_admin
def skip_cmd(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    try:
        nxt = _mc().skip(chat_id)
        if not nxt:
            update.effective_message.reply_text("⏭ Queue empty — stopped playback.")
        else:
            _log_play(chat_id, nxt)
            update.effective_message.reply_text(
                _now_playing_text(nxt),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=_player_kb(),
            )
    except Exception as exc:  # noqa: BLE001
        update.effective_message.reply_text(f"❌ Skip failed: `{exc}`", parse_mode=ParseMode.MARKDOWN)


@user_admin
def stop_cmd(update: Update, context: CallbackContext):
    try:
        _mc().stop(update.effective_chat.id)
        update.effective_message.reply_text("⏹ Stopped and cleared queue.")
    except Exception as exc:  # noqa: BLE001
        update.effective_message.reply_text(f"❌ Stop failed: `{exc}`", parse_mode=ParseMode.MARKDOWN)


def queue_cmd(update: Update, context: CallbackContext):
    q = _mc().get_queue(update.effective_chat.id)
    if not q:
        update.effective_message.reply_text("📭 Queue is empty.")
        return
    lines = [f"*🎵 Queue ({len(q)}):*\n"]
    for i, item in enumerate(q, 1):
        prefix = "▶️" if i == 1 else f"`{i}.`"
        kind = "📹" if item.get("video") else "🎵"
        lines.append(f"{prefix} {kind} `{item['title']}` — _{item['requested_by']}_")
    update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


def player_cmd(update: Update, context: CallbackContext):
    """/player — interactive control panel."""
    chat_id = update.effective_chat.id
    current = _mc().get_current(chat_id)
    if not current:
        update.effective_message.reply_text("❍ Nothing is playing right now.")
        return
    update.effective_message.reply_text(
        _now_playing_text(current),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=_player_kb(),
    )


def topsongs_cmd(update: Update, context: CallbackContext):
    if _topsongs is None:
        update.effective_message.reply_text("❍ Leaderboard requires MongoDB (`MONGO_DB_URI`).")
        return
    chat_id = update.effective_chat.id
    try:
        top = list(
            _topsongs.find({"chat_id": chat_id}).sort("plays", -1).limit(10)
        )
    except Exception as exc:  # noqa: BLE001
        update.effective_message.reply_text(f"❌ Leaderboard error: `{exc}`", parse_mode=ParseMode.MARKDOWN)
        return
    if not top:
        update.effective_message.reply_text("📭 No plays logged yet — start with /play!")
        return
    medals = ["🥇", "🥈", "🥉"] + [f"`{i}.`" for i in range(4, 11)]
    lines = ["*🏆 Top 10 songs in this group*\n"]
    for i, doc in enumerate(top):
        lines.append(f"{medals[i]} `{doc['title']}` — *{doc['plays']}* plays")
    update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


# ---------- inline button callbacks ----------
def player_button(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = query.message.chat
    user_id = query.from_user.id
    action = query.data  # mus_pause / mus_resume / mus_skip / mus_stop / mus_queue

    # Admin gate for control actions
    if action in ("mus_pause", "mus_resume", "mus_skip", "mus_stop"):
        if not is_user_admin(chat, user_id):
            query.answer("Admins only.", show_alert=True)
            return

    mc = _mc()
    try:
        if action == "mus_pause":
            mc.pause(chat.id)
            query.answer("Paused.")
        elif action == "mus_resume":
            mc.resume(chat.id)
            query.answer("Resumed.")
        elif action == "mus_stop":
            mc.stop(chat.id)
            query.answer("Stopped.")
            query.edit_message_text("⏹ Stopped and cleared queue.")
        elif action == "mus_skip":
            nxt = mc.skip(chat.id)
            if not nxt:
                query.answer("Queue empty.")
                query.edit_message_text("⏭ Queue empty — stopped playback.")
            else:
                _log_play(chat.id, nxt)
                query.answer("Skipped.")
                query.edit_message_text(
                    _now_playing_text(nxt),
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=_player_kb(),
                )
        elif action == "mus_queue":
            q = mc.get_queue(chat.id)
            if not q:
                query.answer("Queue is empty.", show_alert=True)
            else:
                preview = "\n".join(
                    f"{i}. {it['title']}" for i, it in enumerate(q[:5], 1)
                )
                query.answer(preview[:200], show_alert=True)
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("player_button error")
        query.answer(f"Error: {exc}", show_alert=True)


# ---------- auto-advance callback (fired from MusicClient on StreamEnded) ----------
def _on_advance(chat_id: int, nxt):
    if nxt is None:
        return
    try:
        _log_play(chat_id, nxt)
        dispatcher.bot.send_message(
            chat_id,
            _now_playing_text(nxt),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_player_kb(),
        )
    except Exception:  # noqa: BLE001
        LOGGER.exception("failed to notify auto-advance")


_mc().on_advance = _on_advance


# ---------- handler registration ----------
dispatcher.add_handler(CommandHandler("play", play_cmd, run_async=True))
dispatcher.add_handler(CommandHandler(["vplay", "vplayforce"], vplay_cmd, run_async=True))
dispatcher.add_handler(CommandHandler("pause", pause_cmd, run_async=True))
dispatcher.add_handler(CommandHandler("resume", resume_cmd, run_async=True))
dispatcher.add_handler(CommandHandler("skip", skip_cmd, run_async=True))
dispatcher.add_handler(CommandHandler(["stop", "end"], stop_cmd, run_async=True))
dispatcher.add_handler(CommandHandler(["queue", "cqueue"], queue_cmd, run_async=True))
dispatcher.add_handler(CommandHandler("player", player_cmd, run_async=True))
dispatcher.add_handler(CommandHandler("topsongs", topsongs_cmd, run_async=True))
dispatcher.add_handler(CallbackQueryHandler(player_button, pattern=r"^mus_", run_async=True))
