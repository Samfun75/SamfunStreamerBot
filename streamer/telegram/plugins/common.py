from .. import Common
from pyrogram import filters, emoji, Client
from pyrogram.types import Message, InlineQuery
from streamer.database.users import StreamerUsers


@Client.on_message(filters.private & filters.command("start", prefixes=["/"]),
                   group=0)
async def start_message_handler(_, m: Message):
    await StreamerUsers().insert_user(m.from_user.id)
    await m.reply_text(
        text=f"Hello! I'm **Samfun Streamer Bot** {emoji.DESKTOP_COMPUTER} \n\n"
        "I can help you live stream telegram files to your channels or groups. \n"
        "Send /help to see how I work.")
    m.stop_propagation()


@Client.on_message(filters.private & filters.command("help", prefixes=["/"]),
                   group=0)
async def help_message_handler(_, m: Message):
    await m.reply_text(
        text="Hello! I'm **Samfun Streamer Bot**\n"
        "Original bot [Samfun Streamer Bot](https://t.me/SamfunStreamerBot)\n"
        "Source [Github](https://github.com/Samfun75/SamfunStreamerBot)\n\n"
        "Here are the commands you can use:\n"
        "/start : Start the bot.\n"
        "/help: Show this helpful message\n\n"
        "To register the chat use this format \n`/register chat_id` (Only for bot owner). \nFor others "
        "use the format \n`/register chat_id stream_url stream_key`\n"
        "E.g /register -1001234567890 or \n/register -100123456789 rtmps://dc1-1.rtmp.t.me/s/ 10909994:xxxxxxx\n"
        "**Note**: you must separate the stream_url and stream_key and you must "
        "recieve a success message or you have to try again!\n\n"
        "You can then send me a video or audio to stream or reply /stream to a video or audio file you already sent me "
        "and I'll play it in your preferred channel or group\n"
        "Note that this bot works in private mode only!",
        disable_web_page_preview=True)
    m.stop_propagation()


@Client.on_message(group=-1)
async def stop_user_from_doing_anything(_, message: Message):
    allowed_users = Common().allowed_users
    if allowed_users:
        if message.chat.id in allowed_users:
            message.continue_propagation()
        else:
            message.stop_propagation()
    else:
        message.continue_propagation()


@Client.on_inline_query(group=-1)
async def stop_user_from_doing_anything_inline(_, iq: InlineQuery):
    allowed_users = Common().allowed_users
    if allowed_users and iq.from_user:
        if iq.from_user.id not in allowed_users:
            iq.stop_propagation()
        else:
            iq.continue_propagation()
    else:
        if iq.from_user:
            iq.continue_propagation()
        else:
            iq.stop_propagation()
