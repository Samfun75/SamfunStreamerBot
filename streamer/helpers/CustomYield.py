from typing import Union
from hashlib import sha256
from pyrogram.crypto import aes
from pyrogram.types import Message
from pyrogram import Client, utils, raw
from streamer.telegram import StreamerBot
from pyrogram.session import Session, Auth
from pyrogram.file_id import FileId, FileType, ThumbnailSource
from pyrogram.errors import AuthBytesInvalid, VolumeLocNotFound, CDNFileHashMismatch


# Code from https://github.com/eyaadh/megadlbot_oss/blob/master/mega/telegram/utils/custom_download.py
class TGCustomYield:

    def __init__(self):
        """ A custom method to stream files from telegram.
        functions:
            generate_file_properties: returns the properties for a media on a specific message contained in FileId class.
            generate_media_session: returns the media session for the DC that contains the media file on the message.
            yield_file: yield a file from telegram servers for streaming.
        """
        self.main_bot = StreamerBot

    @staticmethod
    async def generate_file_properties(msg: Message):
        error_message = "This message doesn't contain any downloadable media"
        available_media = ("audio", "document", "photo", "sticker",
                           "animation", "video", "voice", "video_note")

        if isinstance(msg, Message):
            for kind in available_media:
                media = getattr(msg, kind, None)

                if media is not None:
                    break
            else:
                raise ValueError(error_message)
        else:
            media = msg

        if isinstance(media, str):
            file_id_str = media
        else:
            file_id_str = media.file_id

        file_id_obj = FileId.decode(file_id_str)

        # The below lines are added to avoid a break in routes.py
        setattr(file_id_obj, "file_size", getattr(media, "file_size", 0))
        setattr(file_id_obj, "mime_type", getattr(media, "mime_type", ""))
        setattr(file_id_obj, "file_name", getattr(media, "file_name", ""))

        return file_id_obj

    async def generate_media_session(self, client: Client, msg: Message):
        data = await self.generate_file_properties(msg)

        media_session = client.media_sessions.get(data.dc_id, None)

        if media_session is None:
            if data.dc_id != await client.storage.dc_id():
                media_session = Session(
                    client,
                    data.dc_id,
                    await Auth(client, data.dc_id, await
                               client.storage.test_mode()).create(),
                    await client.storage.test_mode(),
                    is_media=True)
                await media_session.start()

                for _ in range(3):
                    exported_auth = await client.send(
                        raw.functions.auth.ExportAuthorization(
                            dc_id=data.dc_id))

                    try:
                        await media_session.send(
                            raw.functions.auth.ImportAuthorization(
                                id=exported_auth.id,
                                bytes=exported_auth.bytes))
                    except AuthBytesInvalid:
                        continue
                    else:
                        break
                else:
                    await media_session.stop()
                    raise AuthBytesInvalid
            else:
                media_session = Session(client,
                                        data.dc_id,
                                        await client.storage.auth_key(),
                                        await client.storage.test_mode(),
                                        is_media=True)
                await media_session.start()

            client.media_sessions[data.dc_id] = media_session

        return media_session

    @staticmethod
    async def get_location(file_id: FileId):
        file_type = file_id.file_type

        if file_type == FileType.CHAT_PHOTO:
            if file_id.chat_id > 0:
                peer = raw.types.InputPeerUser(
                    user_id=file_id.chat_id,
                    access_hash=file_id.chat_access_hash)
            else:
                if file_id.chat_access_hash == 0:
                    peer = raw.types.InputPeerChat(chat_id=-file_id.chat_id)
                else:
                    peer = raw.types.InputPeerChannel(
                        channel_id=utils.get_channel_id(file_id.chat_id),
                        access_hash=file_id.chat_access_hash)

            location = raw.types.InputPeerPhotoFileLocation(
                peer=peer,
                volume_id=file_id.volume_id,
                local_id=file_id.local_id,
                big=file_id.thumbnail_source == ThumbnailSource.CHAT_PHOTO_BIG)
        elif file_type == FileType.PHOTO:
            location = raw.types.InputPhotoFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size)
        else:
            location = raw.types.InputDocumentFileLocation(
                id=file_id.media_id,
                access_hash=file_id.access_hash,
                file_reference=file_id.file_reference,
                thumb_size=file_id.thumbnail_size)

        return location

    async def yield_file(self, media_msg: Message, offset: int,
                         first_part_cut: int, last_part_cut: int,
                         part_count: int, chunk_size: int) -> Union[str, None]:
        client = self.main_bot
        data = await self.generate_file_properties(media_msg)
        media_session = await self.generate_media_session(client, media_msg)

        current_part = 1

        location = await self.get_location(data)

        r = await media_session.send(raw.functions.upload.GetFile(
            location=location, offset=offset, limit=chunk_size),
                                     sleep_threshold=15)

        if isinstance(r, raw.types.upload.File):
            while current_part <= part_count:
                chunk = r.bytes
                if not chunk:
                    break
                offset += chunk_size
                if part_count == 1:
                    yield chunk[first_part_cut:last_part_cut]
                    break
                if current_part == 1:
                    yield chunk[first_part_cut:]
                if 1 < current_part <= part_count:
                    yield chunk

                r = await media_session.send(raw.functions.upload.GetFile(
                    location=location, offset=offset, limit=chunk_size),
                                             sleep_threshold=15)

                current_part += 1
        elif isinstance(r, raw.types.upload.FileCdnRedirect):

            cdn_session = client.media_sessions.get(r.dc_id, None)

            if cdn_session is None:
                cdn_session = Session(self,
                                      r.dc_id,
                                      await Auth(
                                          self, r.dc_id, await
                                          client.storage.test_mode()).create(),
                                      await client.storage.test_mode(),
                                      is_media=True,
                                      is_cdn=True)

                await cdn_session.start()

                client.media_sessions[r.dc_id] = cdn_session

            while current_part <= part_count:
                r2 = await cdn_session.send(
                    raw.functions.upload.GetCdnFile(file_token=r.file_token,
                                                    offset=offset,
                                                    limit=chunk_size))

                if isinstance(r2, raw.types.upload.CdnFileReuploadNeeded):
                    try:
                        await media_session.send(
                            raw.functions.upload.ReuploadCdnFile(
                                file_token=r.file_token,
                                request_token=r2.request_token))
                    except VolumeLocNotFound:
                        break
                    else:
                        continue

                chunk = r2.bytes

                # https://core.telegram.org/cdn#decrypting-files
                decrypted_chunk = aes.ctr256_decrypt(
                    chunk, r.encryption_key,
                    bytearray(r.encryption_iv[:-4] +
                              (offset // 16).to_bytes(4, "big")))

                hashes = await media_session.send(
                    raw.functions.upload.GetCdnFileHashes(
                        file_token=r.file_token, offset=offset))

                # https://core.telegram.org/cdn#verifying-files
                for i, h in enumerate(hashes):
                    cdn_chunk = decrypted_chunk[h.limit * i:h.limit * (i + 1)]
                    CDNFileHashMismatch.check(
                        h.hash == sha256(cdn_chunk).digest())

                offset += chunk_size
                if part_count == 1:
                    yield decrypted_chunk[first_part_cut:last_part_cut]
                    break
                if current_part == 1:
                    yield decrypted_chunk[first_part_cut:]
                if 1 < current_part <= part_count:
                    yield decrypted_chunk

                r = await media_session.send(raw.functions.upload.GetFile(
                    location=location, offset=offset, limit=chunk_size),
                                             sleep_threshold=15)

                current_part += 1