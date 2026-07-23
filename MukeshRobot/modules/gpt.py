from MukeshRobot import pbot as app
import requests
from pyrogram import *


@app.on_message(filters.command(["chat","ask","gpt"]))
async def gpt(_,message):
    rep = await message.reply_text("💭")
    if len(message.text) < 1:
        return await rep.edit_text("**Give me a query too...**")
    text = message.text.split(maxsplit=1)[1]
    url = "https://lexica.qewertyy.me/models"
    params = {"model_id": 5, "prompt": text}
    resp = requests.post(url , params=params)
    if resp.status_code == 200:
        exe = resp.json()['content']
        return await rep.edit_text(exe)
    else:
        return await rep.edit_text("**Currently API is Down!**")







