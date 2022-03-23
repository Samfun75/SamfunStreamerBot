import math
import time
import asyncio
import logging
from uuid import uuid4
from ffmpeg import FFmpeg
from pyrogram import emoji
from threading import Event
from streamer.helpers import Util
from pyrogram.raw.types.messages import Chats
from streamer.helpers import cancelled
from streamer.database.users import StreamerUsers
from streamer.helpers.CustomYield import TGCustomYield
from pyrogram.raw.functions.channels import GetChannels, GetFullChannel
from streamer.telegram import StreamerBot, StreamerUserBot
from pyrogram.raw.types import UpdateGroupCall, InputGroupCall, InputPeerChannel, Channel
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.raw.functions.phone import CreateGroupCall, GetGroupCallStreamRtmpUrl, DiscardGroupCall
from pyrogram.errors import PeerIdInvalid

logger = logging.getLogger(__name__)
streams = {}


class Stream:

    def __init__(self, media_msg: Message, cb_msg: Message,
                 stream_chat_id: int):
        self.ffmpeg = FFmpeg()
        self.cb_msg = cb_msg
        self.media_msg = media_msg
        self.stream_chat_id = stream_chat_id
        self.cancel = Event()
        self.time = time.time()
        self.peer = None

    async def __get_media_title(self):
        if self.media_msg.audio:
            title = self.media_msg.audio.title
        elif self.media_msg.video:
            title = self.media_msg.video.file_name
        elif self.media_msg.document:
            title = self.media_msg.document.file_name
        else:
            title = 'Livestream'

        return title.replace('_', ' ')

    async def __prepare_stream(self):
        self.user_detail = await StreamerUsers().get_stream_loc(
            self.media_msg.from_user.id)
        # self.user_detail = {
        #     'name': 'Samfun',
        #     'stream_url': 'stream_url1',
        #     'stream_key': 'stream_key1',
        #     'stream_chat_id': '-1001796252658'
        # }
        self.ack_msg = await self.media_msg.reply_text(
            'Preparing Livestream...', quote=True)
        logger.info('Preparing Livestream...')

        try:
            self.peer = await StreamerUserBot.resolve_peer(self.stream_chat_id)
        except PeerIdInvalid:
            logger.warning(f"Chat ID is invalid **{self.stream_chat_id}**")
            raise UnsupportedChat()

        if not isinstance(self.peer, InputPeerChannel):
            logger.warning(
                f"Livestream not supported in this chat {self.stream_chat_id}")
            raise UnsupportedChat()

        r = await StreamerUserBot.send(GetChannels(id=[self.peer]))
        if isinstance(r, Chats):
            if len(r.chats) > 0 and isinstance(r.chats[0], Channel):
                self.channel = r.chats[0]

        logger.info('Preparing ffmpeg...')
        if not self.channel.creator and (
                not (self.user_detail['stream_url']
                     and self.user_detail['stream_key']) or
            (await StreamerUserBot.get_me()).id != self.media_msg.chat.id):
            logger.warning(
                f'rtmps url could not be found for chat {self.stream_chat_id}')
            raise NotCreator()

        if self.channel.creator and (
                await StreamerUserBot.get_me()).id == self.media_msg.chat.id:
            rtmp_obj = await StreamerUserBot.send(
                GetGroupCallStreamRtmpUrl(peer=self.peer, revoke=False))
            stream_url = rtmp_obj.url + rtmp_obj.key
        else:
            stream_url = self.user_detail['stream_url'] + self.user_detail[
                'stream_key']

        self.ffmpeg.option('y').option('re').input('pipe:0').output(
            stream_url,
            {
                'c:v': 'libx264',
                'c:a': 'aac',
                'b:a': '160k',
                'q:v': 0
            },
            preset='veryfast',
            pix_fmt='yuv420p',
            tune='zerolatency',
            vf="pad=ceil(iw/2)*2:ceil(ih/2)*2",  # make hieght even
            crf=18,
            g=50,
            ac=2,
            ar=44100,
            f='flv',
            flvflags='no_duration_filesize')

    async def __start_livestream(self):
        logger.info('Starting Livestream...')
        await self.ack_msg.edit_text('Starting Livestream...')

        if self.channel.call_active:
            await self.ack_msg.edit_text(
                f"A livestream is already being broadcasted at '{self.channel.title}'\n"
                "If the livestream doesn't support rtmps please close and create a new "
                "livestream with rtmps support using desktop telegram.",
                reply_markup=None)
            logger.info(
                f'Skipped livestream creation for chat {self.stream_chat_id}')
            if self.channel.creator and (await StreamerUserBot.get_me()
                                         ).id == self.media_msg.chat.id:
                chat = await StreamerUserBot.send(
                    GetFullChannel(channel=self.peer))
                if chat.full_chat.call:
                    streams[self.stream_chat_id] = chat.full_chat.call
        else:
            if self.channel.creator and (await StreamerUserBot.get_me()
                                         ).id == self.media_msg.chat.id:
                chat = await StreamerUserBot.send(
                    GetFullChannel(channel=self.peer))

                if chat.full_chat.call:
                    await StreamerUserBot.send(
                        DiscardGroupCall(call=chat.full_chat.call))
                    if self.stream_chat_id in streams.keys():
                        streams.pop(self.stream_chat_id)
                    if self.stream_chat_id in cancelled.keys():
                        evt = cancelled.pop(self.stream_chat_id)
                        evt.set()
                resp = await StreamerUserBot.send(
                    CreateGroupCall(peer=self.peer,
                                    random_id=int(str(uuid4().int)[:7]),
                                    title=await self.__get_media_title(),
                                    rtmp_stream=True))
                for update in resp.updates:
                    if isinstance(update, UpdateGroupCall):
                        streams[self.stream_chat_id] = InputGroupCall(
                            id=update.call.id,
                            access_hash=update.call.access_hash)
                        logger.info('Saved groupcall...')
                logger.info('Livestream Created...')
                await self.ack_msg.edit_text(
                    f"A livestream is created at '{self.channel.title}'\n",
                    reply_markup=None)
            else:
                await self.ack_msg.edit_text(
                    f"Please manually create a livestream at '{self.channel.title}'.\n"
                    "Becasue bot owner not creator of the chat.",
                    reply_markup=None)
        cancelled[self.stream_chat_id] = self.cancel

    async def start_stream(self):
        if not (self.media_msg.audio or self.media_msg.video or
                (self.media_msg.document
                 and self.media_msg.document.mime_type.split('/')[0]
                 in ['audio', 'video'])):
            await self.cb_msg.delete()
            await self.ack_msg.edit_text(
                text="I don't think I can stream this type of files "
                f"({self.media_msg.document.mime_type}). {emoji.FACE_IN_CLOUDS}\n"
                "Only **Audio and Video** are allowed.")
            return
        try:
            await self.__prepare_stream()
        except (UnsupportedChat, NotCreator) as e:
            if isinstance(e, UnsupportedChat):
                await self.ack_msg.edit_text(
                    f"Can't start a call in this chat or chat invalid (**{self.channel.title})**",
                    reply_markup=None)
                logger.warning(
                    f"Can't start a call in this chat or chat invalid {self.stream_chat_id}"
                )
            else:
                await self.ack_msg.edit_text(
                    "**Can't get rtmps url for this chat**\n"
                    "The bot owner account is not an owner of the chat and "
                    f"no stream_url or stream_key provided for chat **{self.channel.title}**",
                    reply_markup=None)
                logger.info(
                    f"Can't get rtmps url for this chat {self.stream_chat_id})"
                )
            return

        logger.info('Preparing File...')
        await self.ack_msg.edit_text('Preparing File...', reply_markup=None)
        try:
            file_properties = await TGCustomYield().generate_file_properties(
                self.media_msg)
        except ValueError as e:
            await self.ack_msg.edit_text(f'{e}', reply_markup=None)
            return

        from_bytes = 0
        req_bytes = file_properties.file_size - 1

        new_chunk_size = await Util.chunk_size(req_bytes)
        offset = await Util.offset_fix(from_bytes, new_chunk_size)
        first_part_cut = from_bytes - offset
        last_part_cut = (req_bytes % new_chunk_size) + 1
        part_count = math.ceil(req_bytes / new_chunk_size)
        body = TGCustomYield().yield_file(self.media_msg, offset,
                                          first_part_cut, last_part_cut,
                                          part_count, new_chunk_size)

        self.ffmpeg.add_listener('progress', self.__on_progress)
        self.ffmpeg.add_listener('completed', self.__on_completed)
        self.ffmpeg.add_listener('error', self.__on_error)
        self.ffmpeg.add_listener('stderr', self.__on_stderr)
        self.ffmpeg.add_listener('terminated', self.__on_terminate)
        self.reader = asyncio.StreamReader()
        await self.__start_livestream()
        task = StreamerBot.loop.create_task(
            self.ffmpeg.execute(stream=self.reader))

        try:
            async for file_byte in body:
                if self.cancel.is_set():
                    break
                if file_byte is not None:
                    self.reader.feed_data(file_byte)
                else:
                    self.reader.feed_eof()
                    break
            await task
        except BrokenPipeError:
            logger.info('BrokenPipeError Caught.')
        except Exception as e:
            logger.error(e)
        logger.info('All Streaming Processes Done!')

    def __on_terminate(self):
        logger.info('Stream Terminated!')

    def __on_progress(self, progress):
        if self.cancel.is_set():
            self.ffmpeg.remove_all_listeners('progress')
            self.reader.feed_eof()
            self.ffmpeg.terminate()
            if self.stream_chat_id in cancelled.keys():
                cancelled.pop(self.stream_chat_id)
            if self.stream_chat_id in streams.keys():
                call = streams.pop(self.stream_chat_id)
                StreamerBot.loop.create_task(
                    StreamerUserBot.send(DiscardGroupCall(call=call)))
                logger.info(f'Discarding GroupCall')

            StreamerBot.loop.create_task(
                self.ack_msg.edit_text(text='Stream Terminated!',
                                       reply_markup=None))

            return
        if time.time() - self.time > 3:
            StreamerBot.loop.create_task(
                self.ack_msg.edit_text(
                    text=str(progress),
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            text=f'{emoji.NO_ENTRY} Stop the Stream',
                            callback_data=f'cancel_{self.stream_chat_id}')
                    ]])))
            self.time = time.time()

    def __on_completed(self):
        if self.stream_chat_id in cancelled.keys():
            cancelled.pop(self.stream_chat_id)
        if self.stream_chat_id in streams.keys():
            call = streams.pop(self.stream_chat_id)
            StreamerBot.loop.create_task(
                StreamerUserBot.send(DiscardGroupCall(call=call)))
            logger.info(f'Discarding GroupCall')
        StreamerBot.loop.create_task(
            self.ack_msg.edit_text(text='Stream Completed', reply_markup=None))
        logger.info('Stream Completed')

    def __on_error(self, code):
        if self.stream_chat_id in cancelled.keys():
            cancelled.pop(self.stream_chat_id)
        if self.stream_chat_id in streams.keys():
            call = streams.pop(self.stream_chat_id)
            StreamerBot.loop.create_task(
                StreamerUserBot.send(DiscardGroupCall(call=call)))
            logger.info(f'Discarding GroupCall')
        StreamerBot.loop.create_task(
            self.ack_msg.edit_text(
                text=f'Error Occured... **Code: {code}**\n'
                'If this keeps happening please report it to @Samfun75'))
        logger.error(f'Error Occured: {code}')

    def __on_stderr(self, line):
        logger.debug('ffmpeg:' + str(line))


class UnsupportedChat(Exception):
    pass


class NotCreator(Exception):
    pass