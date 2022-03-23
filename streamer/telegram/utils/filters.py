from pyrogram import Client
from pyrogram.filters import *
from pyrogram.types import CallbackQuery, Message


def callback_query(args: str, payload=True):
    """
    Accepts arg at all times.

    If payload is True, extract payload from callback and assign to callback.payload
    If payload is False, only check if callback exactly matches argument
    """

    async def func(ftl, __, query: CallbackQuery):
        if payload:
            thing = r"{}\_"
            if re.search(re.compile(thing.format(ftl.data)), query.data):
                search = re.search(re.compile(r"\_{1}(.*)"), query.data)
                if search:
                    query.payload = search.group(1)
                else:
                    query.payload = None

                return True

            return False
        else:
            if ftl.data == query.data:
                return True

            return False

    return create(func, 'CustomCallbackQuery', data=args)


def document_filter():
    """Return a filter for a document with acceptable video type"""

    async def func(_, c: Client, m: Message):
        if m.document and m.document.mime_type.split('/')[0] in [
                'audio', 'video'
        ]:
            return True
        else:
            return False

    return create(func, 'CustomVideoFilter')


def reply_media_filter():
    """Return a filter that checks if a message is a reply and that reply have acceptable media"""

    async def func(_, c: Client, m: Message):
        if m.reply_to_message:
            if m.reply_to_message.audio or m.reply_to_message.video or (
                    m.reply_to_message.document
                    and m.reply_to_message.document.mime_type.split('/')[0]
                    in ['audio', 'video']):
                return True
            return False
        else:
            return False

    return create(func, 'CustomReplyFilter')


def command_args_filter():
    """Return a filter that checks if a command have arguments"""

    async def func(_, c: Client, m: Message):
        if m.command and len(m.command) > 1:
            return True
        else:
            return False

    return create(func, 'CustomCommandArgsFilter')