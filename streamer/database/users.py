from streamer.database import StreamerDB
from pymongo.errors import WriteError


class StreamerUsers:

    def __init__(self):
        """
        BookdlUsers is the mongo collection for the documents that holds the details of the users.

        Functions:
            insert_user: insert new documents, that contains the details of the new users who started using the bot.

            get_user: return the document that contains the user_id for the the given telegram user id.

        """
        self.user_collection = StreamerDB().db['Users']

    async def insert_user(self, user_id: int):
        if self.user_collection.count_documents({'user_id': user_id}) > 0:
            return
        else:
            self.user_collection.insert_one({
                'user_id': user_id,
                'stream_locations': [],
            })

    async def get_user(self, user_id: int):
        return self.user_collection.find_one({'user_id': user_id})

    async def add_stream_loc(self, user_id: int, stream_chat_id: int,
                             name: str, stream_url: str, stream_key: str):
        try:
            res = self.user_collection.update_one({'user_id': user_id}, {
                '$push': {
                    'stream_locations': {
                        'name': name,
                        'stream_url': stream_url,
                        'stream_key': stream_key,
                        'stream_chat_id': stream_chat_id
                    }
                }
            })
        except WriteError as e:
            None, e.details
        return res, None

    async def remove_stream_loc(self,
                                user_id: int,
                                stream_chat_id: int = None):
        try:
            if stream_chat_id:
                query = {
                    '$pull': {
                        'stream_locations': {
                            'stream_chat_id': stream_chat_id
                        }
                    }
                }
            else:
                query = {'$set': {'stream_locations': []}}

            res = self.user_collection.update_one({'user_id': user_id}, query)

        except WriteError as e:
            None, e.details
        return res, None

    async def get_stream_loc(self, user_id: int, stream_chat_id: int = None):
        res = (await self.get_user(user_id))['stream_locations']
        if not stream_chat_id:
            return res
        else:
            return next(
                (loc
                 for loc in res if loc['stream_chat_id'] == stream_chat_id),
                None)
