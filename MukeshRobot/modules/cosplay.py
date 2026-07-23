import requests
from pyrogram import filters
from pyrogram.types import Message,InlineKeyboardButton,InlineKeyboardMarkup
from pyrogram.enums import *

from telegram.ext import run_async

from MukeshRobot import pbot as app

url_nsfw = "https://api.waifu.pics/nsfw/"


@app.on_message(filters.command("cosplay"))
async def cosplay(_,msg):
    img = requests.get("https://waifu-api.vercel.app").json()
    await msg.reply_photo(img, caption=f"Cosplay By @{app.me.username}")



@app.on_message(filters.command("ncosplay"))
async def ncosplay(_,msg):
    if msg.chat.type != ChatType.PRIVATE:
      await msg.reply_text("Sorry you can use this command only in private chat with bot",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Go PM",url=f"https://t.me/{app.me.username}?start=True")]
            ]
        ))
    else:
       ncosplay = requests.get("https://waifu-api.vercel.app/items/1").json()

       await msg.reply_photo(ncosplay, caption=f"Ncosplay By @{app.me.username}")

__mod_name__ ="cosplay.py"
__help__ ="To get random cosplay use /cosplay for swf cosplay and use /ncosplay for NSFW cosplay"

