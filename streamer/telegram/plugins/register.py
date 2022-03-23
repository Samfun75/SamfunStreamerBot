import re
from ..utils import filters
from pyrogram import emoji, Client
from pyrogram.raw.types.messages import Chats
from streamer.telegram import StreamerUserBot
from streamer.database.users import StreamerUsers
from pyrogram.raw.functions.channels import GetChannels
from pyrogram.raw.types import InputPeerChannel, Channel
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import PeerIdInvalid

sURL_regex = re.compile(r"^\d{10}:[a-zA-Z0-9_-]{22}", re.IGNORECASE)
sKey_regex = remove_reg = re.compile(r"^\d{10}:[a-zA-Z0-9_-]{22}",
                                     re.IGNORECASE)


@Client.on_callback_query(filters.callback_query("unregister"))
async def unregister_callback_handler(c: Client, cb: CallbackQuery):
    params = cb.payload.split('_')
    if len(params) > 0:
        if params[0] == 'all':
            res, err = await StreamerUsers().remove_stream_loc(cb.from_user.id)
        else:
            stream_chat_id = int(params[0]) if len(params) > 0 else None
            res, err = await StreamerUsers().remove_stream_loc(
                cb.from_user.id, stream_chat_id)
    else:
        await cb.answer("There is a problem with this callback!",
                        show_alert=True)
        await cb.message.delete()
        return
    if res and res.acknowledged:
        await cb.answer("Stream chat successfully removed!", show_alert=True)
        stream_locs = await StreamerUsers().get_stream_loc(cb.from_user.id)
        if stream_locs:
            inline_buttons = []
            for loc in stream_locs:
                inline_buttons.append([
                    InlineKeyboardButton(
                        text=f"{emoji.CROSS_MARK} {loc['name']}",
                        callback_data=f"unregister_{loc['stream_chat_id']}")
                ])
            inline_buttons.append([
                InlineKeyboardButton(
                    text=f"Remove All {emoji.DOUBLE_EXCLAMATION_MARK}",
                    callback_data="unregister_all")
            ])
            await cb.message.edit_reply_markup(
                InlineKeyboardMarkup(inline_buttons))
        else:
            await cb.message.edit_text(
                text=f'{emoji.OPEN_FILE_FOLDER} No chats registered!',
                reply_markup=None)
    else:
        await cb.message.reply_text(
            "The following error has occured when removing stream chat\n"
            f"{err or res.raw_result}",
            quote=True)


@Client.on_message(filters.private
                   & filters.command("unregister", prefixes=["/"]),
                   group=0)
async def unregister_command_handler(_, m: Message):
    stream_locs = await StreamerUsers().get_stream_loc(m.from_user.id)
    if stream_locs:
        inline_buttons = []
        for loc in stream_locs:
            inline_buttons.append([
                InlineKeyboardButton(
                    text=f"{emoji.CROSS_MARK} {loc['name']}",
                    callback_data=f"unregister_{loc['stream_chat_id']}")
            ])
        inline_buttons.append([
            InlineKeyboardButton(
                text=f"Remove All {emoji.DOUBLE_EXCLAMATION_MARK}",
                callback_data="unregister_all")
        ])
        await m.reply_text('Which chats do you want to remove?',
                           reply_markup=InlineKeyboardMarkup(inline_buttons))
    else:
        await m.reply_text(
            text=f'{emoji.OPEN_FILE_FOLDER} No chats registered!', quote=True)
    m.stop_propagation()


@Client.on_message(filters.private
                   & filters.command("register", prefixes=["/"])
                   & filters.command_args_filter(),
                   group=0)
async def register_command_handler(_, m: Message):
    try:
        try:
            stream_chat_id = int(m.command[1])
        except ValueError:
            await m.reply_text(
                text=f'{emoji.FACE_WITH_ROLLING_EYES} The provide chat_id '
                f'is not an integer {m.command[1]}',
                quote=True)
            return

        stream_loc = await StreamerUsers().get_stream_loc(
            m.from_user.id, stream_chat_id)
        if stream_loc:
            await m.reply_text(
                f"This chat is already registered!\n"
                f"Chat: **{stream_chat_id}**",
                quote=True)
            return
        try:
            peer = await StreamerUserBot.resolve_peer(stream_chat_id)
        except PeerIdInvalid:
            await m.reply_text(f"Chat ID is invalid **{stream_chat_id}**",
                               quote=True)
            return

        if not isinstance(peer, InputPeerChannel):
            await m.reply_text("Can't start a call in this chat!", quote=True)
            return

        channel = None
        r = await StreamerUserBot.send(GetChannels(id=[peer]))
        if isinstance(r, Chats):
            if len(r.chats) > 0 and isinstance(r.chats[0], Channel):
                channel = r.chats[0]
        if not channel:
            await m.reply_text(
                f"Trouble getting information about this chat "
                f"**{stream_chat_id}** make sure the bot owner have is the owner of this chat!",
                quote=True)
            return

        if channel.creator:
            res, err = await StreamerUsers().add_stream_loc(
                m.from_user.id, stream_chat_id, channel.title, '', '')
        elif len(m.command) > 3:
            stream_url = m.command[2]
            stream_key = m.command[3]

            url_match = sURL_regex.match(stream_url)
            key_match = sKey_regex.match(stream_key)
            if url_match and key_match:
                res, err = await StreamerUsers().add_stream_loc(
                    m.from_user.id, stream_chat_id, channel.title, stream_url,
                    stream_key)
            else:
                await m.reply_text(
                    "The provided stream url and key does not match with telegram's pattern!\n"
                    f"**({stream_url},{stream_key})** make sure copy correctly and use the correct format!",
                    quote=True)
                return
        else:
            await m.reply_text(
                "Bot owner not creator of chat and argument for not creators is too short! "
                "Please use the correct format.\n"
                f"`Arguments: {m.command}\n"
                "Send /help to know more.",
                quote=True)
            return

        if res and res.acknowledged:
            await m.reply_text("Stream chat successfully registered!",
                               quote=True)
        else:
            await m.reply_text(
                "The following error has occured when registering stream chat\n"
                f"{err or res.raw_result}",
                quote=True)
    finally:
        m.stop_propagation()


@Client.on_message(filters.private
                   & filters.command("register", prefixes=["/"]),
                   group=1)
async def register_command_all_handler(_, m: Message):
    await m.reply_text(
        text=f'You need to provide a chat_id {emoji.FACE_WITH_STEAM_FROM_NOSE}\n'
        'e.g. /register -100123456789 (Only applicable if bot you are bot owner)\n\n'
        'If you are not a bot owner, you need to also provide stream url and key\n'
        'e.g. /register -100123456789 -100123456789 rtmps://dc1-1.rtmp.t.me/s 10909994:xxxxxxx\n\n'
        '**Note** that the stream url and key are separeted with and space.',
        quote=True)
    m.stop_propagation()
