from ..utils import filters
from pyrogram import emoji, Client
from streamer.database.users import StreamerUsers
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton


@Client.on_message(filters.private & filters.text, group=2)
async def new_messages_handler(_, m: Message):
    await StreamerUsers().insert_user(m.from_user.id)
    await m.reply_text(text="I don't work this way. "
                       "Send /help to see how I work.")


@Client.on_message(filters.private & filters.document, group=2)
async def new_documents_handler(_, m: Message):
    await m.reply_text(text="I don't think I can stream this type of file "
                       f"({m.document.mime_type}). {emoji.FACE_IN_CLOUDS}\n"
                       "Only Audios and Videos are allowed.",
                       quote=True)


@Client.on_message(filters.private &
                   (filters.audio | filters.video | filters.document_filter()),
                   group=0)
async def new_stream_files_handler(_, m: Message):
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
                        f"stream_{stream_locations[i]['stream_chat_id']}_{m.chat.id}_{m.message_id}"
                    )
                ])
                if len(stream_locations) > i + 1:
                    inline_buttons[int(i / 2) if i > 0 else i].append(
                        InlineKeyboardButton(
                            text=
                            f"{emoji.MOUNT_FUJI} {stream_locations[i+1]['name']}",
                            callback_data=
                            f"stream_{stream_locations[i+1]['stream_chat_id']}_{m.chat.id}_{m.message_id}"
                        ))
        await m.reply_text(
            text='Which chat do you want me to stream this file?',
            reply_markup=InlineKeyboardMarkup(inline_buttons),
            quote=True)
    else:
        await m.reply_text(
            text='You have not registered any group/channel for stream.\n'
            'Please register at least one chat and reply /stream to this file or send it again.\n'
            f'Send /help to see how you can register a chat {emoji.VICTORY_HAND}',
            quote=True)

    m.stop_propagation()
