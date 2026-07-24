import html
import json
import os
import re
from time import sleep

import requests
from telegram import (
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    Update,
    User,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.utils.helpers import mention_html

import MukeshRobot.modules.sql.chatbot_sql as sql
from MukeshRobot import BOT_ID, BOT_NAME, BOT_USERNAME, dispatcher
from MukeshRobot.modules.helper_funcs.chat_status import user_admin, user_admin_no_reply
from MukeshRobot.modules.log_channel import gloggable

# --- Chatbot API (replaces deprecated MukeshAPI) ---
# Set CHATBOT_API_URL in your environment for a custom chatbot endpoint.
# The endpoint should accept a GET/POST with a "message" param and return JSON
# with a "results" or "response" key.
CHATBOT_API_URL = os.environ.get("CHATBOT_API_URL", "")


def _chatbot_reply(text: str) -> str:
    """Get a chatbot response. Falls back gracefully if no API is configured."""
    if not CHATBOT_API_URL:
        return "Chatbot API not configured. Ask the bot owner to set CHATBOT_API_URL."
    try:
        resp = requests.get(
            CHATBOT_API_URL,
            params={"message": text, "mode": "gf"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", data.get("response", data.get("reply", "🤔")))
    except Exception:
        return "Sorry, I'm having trouble connecting to the chat service right now."


@user_admin_no_reply
@gloggable
def mukeshrm(update: Update, context: CallbackContext) -> str:
    query: CallbackQuery = update.callback_query
    user: User = update.effective_user
    match = re.match(r"rm_chat\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat: Chat = update.effective_chat
        is_mukesh = sql.set_mukesh(chat.id)
        if is_mukesh:
            is_mukesh = sql.set_mukesh(user_id)
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"\u1d00\u026a \u1d05\u026a\ua731\u1d00\u0299\u029f\u1d07\u1d05\n"
                f"<b>\u1d00\u1d05\u1d0d\u026a\u0274 :</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            )
        else:
            update.effective_message.edit_text(
                "{} \u1d04\u029c\u1d00\u1d1b\u0299\u1d0f\u1d1b \u1d05\u026as\u1d00\u0299\u029f\u1d07\u1d05 \u0299\u028f {}.".format(
                    dispatcher.bot.first_name, mention_html(user.id, user.first_name)
                ),
                parse_mode=ParseMode.HTML,
            )

    return ""


@user_admin_no_reply
@gloggable
def mukeshadd(update: Update, context: CallbackContext) -> str:
    query: CallbackQuery = update.callback_query
    user: User = update.effective_user
    match = re.match(r"add_chat\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat: Chat = update.effective_chat
        is_mukesh = sql.rem_mukesh(chat.id)
        if is_mukesh:
            is_mukesh = sql.rem_mukesh(user_id)
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"\u1d00\u026a \u1d07\u0274\u1d00\u0299\u029f\u1d07\n"
                f"<b>\u1d00\u1d05\u1d0d\u026a\u0274 :</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            )
        else:
            update.effective_message.edit_text(
                "{} \u1d04\u029c\u1d00\u1d1b\u0299\u1d0f\u1d1b \u1d07\u0274\u1d00\u0299\u029f\u1d07\u1d05 \u0299\u028f {}.".format(
                    dispatcher.bot.first_name, mention_html(user.id, user.first_name)
                ),
                parse_mode=ParseMode.HTML,
            )

    return ""


@user_admin
@gloggable
def mukesh(update: Update, context: CallbackContext):
    message = update.effective_message
    msg = "\u2022 \u1d04\u029c\u1d0f\u1d0fss \u1d00\u0274 \u1d0f\u1d29\u1d1b\u026a\u1d0f\u0274 \u1d1b\u1d0f \u1d07\u0274\u1d00\u0299\u029f\u1d07/\u1d05\u026as\u1d00\u0299\u029f\u1d07 \u1d04\u029c\u1d00\u1d1b\u0299\u1d0f\u1d1b"
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="\u1d07\u0274\u1d00\u0299\u029f\u1d07", callback_data="add_chat({})"),
                InlineKeyboardButton(text="\u1d05\u026as\u1d00\u0299\u029f\u1d07", callback_data="rm_chat({})"),
            ],
        ]
    )
    message.reply_text(
        text=msg,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


def mukesh_message(context: CallbackContext, message):
    reply_message = message.reply_to_message
    if message.text.lower() == "mukesh":
        return True
    elif BOT_USERNAME in message.text.upper():
        return True
    elif reply_message:
        if reply_message.from_user.id == BOT_ID:
            return True
    else:
        return False


def chatbot(update: Update, context: CallbackContext):
    message = update.effective_message
    chat_id = update.effective_chat.id
    bot = context.bot
    is_mukesh = sql.is_mukesh(chat_id)
    if is_mukesh:
        return

    if message.text and not message.document:
        if not mukesh_message(context, message):
            return
        bot.send_chat_action(chat_id, action="typing")
        reply = _chatbot_reply(message.text)
        message.reply_text(reply)


CHATBOTK_HANDLER = CommandHandler("chatbot", mukesh, run_async=True)
ADD_CHAT_HANDLER = CallbackQueryHandler(mukeshadd, pattern=r"add_chat", run_async=True)
RM_CHAT_HANDLER = CallbackQueryHandler(mukeshrm, pattern=r"rm_chat", run_async=True)
CHATBOT_HANDLER = MessageHandler(
    Filters.text
    & (~Filters.regex(r"^#[^\s]+") & ~Filters.regex(r"^!") & ~Filters.regex(r"^\/")),
    chatbot,
    run_async=True,
)

dispatcher.add_handler(ADD_CHAT_HANDLER)
dispatcher.add_handler(CHATBOTK_HANDLER)
dispatcher.add_handler(RM_CHAT_HANDLER)
dispatcher.add_handler(CHATBOT_HANDLER)

__handlers__ = [
    ADD_CHAT_HANDLER,
    CHATBOTK_HANDLER,
    RM_CHAT_HANDLER,
    CHATBOT_HANDLER,
]
