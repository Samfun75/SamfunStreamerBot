import math

cancelled = {}


class Util:

    @staticmethod
    async def chunk_size(length):
        return 2**max(min(math.ceil(math.log2(length / 1024)), 10), 2) * 1024

    @staticmethod
    async def offset_fix(offset, chunksize):
        offset -= offset % chunksize
        return offset
