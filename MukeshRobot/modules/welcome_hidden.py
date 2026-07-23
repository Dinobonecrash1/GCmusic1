import shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
from unidecode import unidecode
import asyncio, os, random, glob
from pyrogram import filters
from pyrogram.types import *
from pyrogram.enums import ParseMode, ChatMemberStatus
from .. import pbot as Mukesh, BOT_USERNAME

from pytz import timezone
from datetime import datetime
from urllib.request import urlopen

img_list = [
    "https://graph.org//file/097531769fdd405480e59.jpg",
    "https://graph.org//file/fb12eda9238d49f937eff.jpg",
    "https://graph.org//file/3722679374ed1b56c03e2.jpg",
    "https://graph.org//file/725b0376a8b2f96bc3237.jpg",
    "https://graph.org//file/483972408aa4822b37bfa.jpg",
    "https://graph.org//file/74a85d290f10da5b8e2de.jpg",
]

ADD_ME = [
    [
        InlineKeyboardButton(
            text="➕ᴀᴅᴅ ᴍᴇ➕",
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true",
        )
    ]
]

def thumbnail(chatimg, userimg, background, welcomemsg, userinfo):
    try:
        def create_thumbnail(userimg):
            x = Image.open(userimg)
            x.thumbnail((300, 300))
            x.save("thumbnail.jpg")
            thumb = Image.open("thumbnail.jpg")
            constrast = ImageEnhance.Contrast(thumb)
            thumb = constrast.enhance(1.5)
            draw = ImageDraw.Draw(thumb)
            height, width = thumb.size
            lum_img = Image.new("L", thumb.size, 0)
            draw = ImageDraw.Draw(lum_img)
            draw.pieslice([(0, 0), (height, width)], 0, 360, fill=255, outline="white")

            img_arr = np.array(thumb)
            lum_img_arr = np.array(lum_img)

            final_img_arr = np.dstack((img_arr, lum_img_arr))
            thumbn = Image.fromarray(final_img_arr)

            return thumbn

        x = create_thumbnail(chatimg)
        y = create_thumbnail(userimg)
        bg = Image.open(background)
        bg = bg.filter(ImageFilter.BoxBlur(8))
        combine = bg.copy()
        combine.paste(x, (80, 132), mask=x)
        combine.paste(y, (870, 132), mask=y)
        combine.save("ok.png")

        def add_text_to_image():
            img = Image.open("ok.png")
            d1 = ImageDraw.Draw(img)
            font = "MukeshRobot/resources/default.ttf"
            my_font = ImageFont.truetype(font, size=60)
            my_font2 = ImageFont.truetype(font, size=40)

            d1.line((300, 570, 1000, 570), fill="white", width=4)

            d1.arc((72, 130, 380, 435), start=0, end=360, fill="#0b0d0c", width=8)
            d1.arc((862, 130, 1170, 435), start=0,
                   end=360, fill="black", width=8)
            d1.text((300, 50), welcomemsg, font=my_font, fill=(224, 224, 224), stroke_width=2, stroke_fill="#f50727")

            d1.multiline_text((500, 580), userinfo,
                              font=my_font2, fill=(224, 224, 224), stroke_width=2, stroke_fill="#f50727")

            im1 = img.crop((0, 0, 1280, 720))

            im1.save("final.jpg")

        add_text_to_image()

    except Exception as e:
        print(e)


@Mukesh.on_chat_member_updated(filters.group)
async def member_has_joined(c: Mukesh, member: ChatMemberUpdated):

    back_img = urlopen(random.choice(img_list))

    # Check if new user joined and is valid
    if (
        member.new_chat_member
        and not member.old_chat_member
        and not member.new_chat_member.user.is_bot
        and member.new_chat_member.user.status
        not in [ChatMemberStatus.BANNED, ChatMemberStatus.RESTRICTED, ChatMemberStatus.LEFT]
    ):
        pass
    else:
        return

    user = member.new_chat_member.user if member.new_chat_member else member.from_user

    user_photo_id = user.photo.big_file_id if user.photo else None
    chat_photo_id = member.chat.photo.big_file_id if member.chat.photo else None
    chat_title = unidecode(member.chat.title)
    username = "@" + user.username if user.username else None
    fullname = user.first_name + (" " + user.last_name if user.last_name else "")
    name = unidecode(fullname)
    ind_time = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')

    if not (user_photo_id or chat_photo_id):
        # No photos to show, just send welcome text
        return await c.send_message(
            member.chat.id,
            f"""<b><u>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ {member.chat.title} </u>
ɴᴀᴍᴇ : {fullname[:45]}
ᴜꜱᴇʀ ɪᴅ : <code>{user.id}</code>
ᴜꜱᴇʀɴᴀᴍᴇ : <code>{username}</code>
ᴍᴇɴᴛɪᴏɴ : {user.mention("ʟɪɴᴋ")}
ᴊᴏɪɴᴇᴅ ᴀᴛ: {ind_time} </b>""",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(ADD_ME),
        )

    # Download photos safely
    chatphoto = await c.download_media(chat_photo_id) if chat_photo_id else None
    userphoto = await c.download_media(user_photo_id) if user_photo_id else None

    info = f" Name  :  {name}\n\nUser id  : {user.id}"

    if not userphoto:
        userphoto = urlopen("https://te.legra.ph/file/f72a978a5c26bf59fadf8.jpg")

    thumbnail(
        chatphoto or urlopen(random.choice(img_list)),  # fallback background
        userphoto,
        back_img,
        welcomemsg=f"welcome to {chat_title}",
        userinfo=info,
    )

    await c.send_photo(
        member.chat.id,
        photo="final.jpg",
        caption=f"""<b><u>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ {member.chat.title} </u>
ɴᴀᴍᴇ : {fullname[:45]}
ᴜꜱᴇʀ ɪᴅ : <code>{user.id}</code>
ᴜꜱᴇʀɴᴀᴍᴇ : <code>{username}</code>
ᴍᴇɴᴛɪᴏɴ : {user.mention("ʟɪɴᴋ")}
ᴊᴏɪɴᴇᴅ ᴀᴛ: {ind_time} </b>""",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(ADD_ME),
    )

    # Cleanup files safely
    try:
        for file in ["ok.png", "final.jpg", "thumbnail.jpg"]:
            if os.path.exists(file):
                os.remove(file)
        if chatphoto and os.path.exists(chatphoto):
            os.remove(chatphoto)
        if userphoto and os.path.exists(userphoto):
            os.remove(userphoto)
        if os.path.exists("downloads"):
            shutil.rmtree("downloads")
    except Exception as e:
        print(f"Cleanup error: {e}")
