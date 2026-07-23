# SOURCE https://github.com/Team-ProjectCodeX
# CREATED BY https://t.me/O_okarma
# PROVIDED BY https://t.me/ProjectCodeX


import requests
from pyrogram import filters
from pyrogram.types import Message

from MukeshRobot import pbot as app

DOWNLOADING_STICKER_ID = (
    "CAACAgIAAxkBAAEDv_xlJWmh2-fKRwvLywJaFeGy9wmBKgACVQADr8ZRGmTn_PAl6RC_MAQ"
)
API_URL = "https://karma-api2.vercel.app/instadl"  # API URL


@app.on_message(
    filters.command(["ig", "instagram", "insta", "instadl"])
)
async def instadl_command_handler(_, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /instadl [Instagram URL]")
        return

    link = message.command[1]
    try:
        downloading_sticker = await message.reply_sticker(DOWNLOADING_STICKER_ID)

        # Make a GET request to the API
        response = requests.get(API_URL, params={"url": link})
        data = response.json()

        # Check if the API request was successful
        if "content_url" in data:
            content_url = data["content_url"]

            # Determine content type from the URL
            content_type = "video" if "video" in content_url else "photo"

            # Reply with either photo or video
            if content_type == "photo":
                await message.reply_photo(content_url)
            elif content_type == "video":
                await message.reply_video(content_url)
            else:
                await message.reply("Unsupported content type.")
        else:
            await message.reply(
                "Unable to fetch content. Please check the Instagram URL."
            )

    except Exception as e:
        print(e)
        await message.reply("An error occurred while processing the request.")

    finally:
        await downloading_sticker.delete()
