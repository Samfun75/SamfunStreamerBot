from threading import Event
from ..utils import filters
from pyrogram import emoji, Client
from streamer.helpers import cancelled
from streamer.helpers.FFmpeg import Stream
from streamer.database.users import StreamerUsers
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton


@Client.on_callback_query(filters.callback_query("stream"))
async def stream_callback_handler(c: Client, cb: CallbackQuery):
    params = cb.payload.split('_')
    if len(params) < 1:
        await cb.answer("There is a problem with this callback!",
                        show_alert=True)
        await cb.message.delete()
        return

    stream_chat_id = int(params[0]) if len(params) > 0 else None
    msg_chat_id = int(params[1]) if len(params) > 1 else None
    msg_id = int(params[2]) if len(params) > 2 else None
    org_msg = await c.get_messages(msg_chat_id,
                                   msg_id) if msg_id is not None else None
    if org_msg:
        await cb.answer('About to start livestream preparation...')
    else:
        await cb.answer(
            'Could not find the message! \n'
            'Please send the media again',
            show_alert=True)
        return
    await Stream(org_msg, cb.message, stream_chat_id).start_stream()


@Client.on_message(filters.private & filters.reply
                   & filters.command("stream", prefixes=["/"])
                   & filters.reply_media_filter(),
                   group=0)
async def stream_command_handler(_, m: Message):
    stream_locations = await StreamerUsers().get_stream_loc(m.from_user.id)
    if stream_locations:
        inline_buttons = []
        for i, _ in enumerate(stream_locations):
            if i % 2 == 0:
                inline_buttons.append([
                    InlineKeyboardButton(
                        text=
                        f"{emoji.MOUNT_FUJI} {stream_locations[i]['name']}",
                        callback_data=
                        f"stream_{stream_locations[i]['stream_chat_id']}_{m.reply_to_message.chat.id}_{m.reply_to_message.message_id}"
                    )
                ])
                if len(stream_locations) > i + 1:
                    inline_buttons[int(i / 2) if i > 0 else i].append(
                        InlineKeyboardButton(
                            text=
                            f"{emoji.MOUNT_FUJI} {stream_locations[i+1]['name']}",
                            callback_data=
                            f"stream_{stream_locations[i+1]['stream_chat_id']}_{m.reply_to_message.chat.id}_{m.reply_to_message.message_id}"
                        ))
        await m.reply_to_message.reply_text(
            text='Which chat do you want me to stream this file?',
            reply_markup=InlineKeyboardMarkup(inline_buttons),
            quote=True)
    else:
        await m.reply_to_message.reply_text(
            text='You have not registered any group/channel for stream.\n'
            'Please register at least one chat and reply /stream to this file or send it again.\n'
            f'Send /help to see how you can register a chat {emoji.VICTORY_HAND}',
            quote=True)
    m.stop_propagation()


@Client.on_message(filters.private
                   & filters.command("stream", prefixes=["/"]),
                   group=1)
async def stream_command_all_handler(_, m: Message):
    if m.reply_to_message:
        text = 'Only Audios and Videos are allowed.'
    else:
        text = 'You must send this command as a reply to a streamable file!'
    await m.reply_text(text=text, quote=True)
    m.stop_propagation()


@Client.on_callback_query(filters.callback_query("cancel"))
async def cancel_callback_handler(c: Client, cb: CallbackQuery):
    params = cb.payload.split('_')
    if len(params) < 1:
        await cb.answer("There is a problem with this callback!",
                        show_alert=True)
        await cb.message.delete()
        return

    stream_chat_id = int(params[0]) if len(params) > 0 else None
    if stream_chat_id in cancelled.keys():
        evt = cancelled[stream_chat_id]
        evt.set()
    await cb.answer('Stream Cancelled Successfuly!')
