import logging
from pyrogram import idle
from streamer.telegram import StreamerBot, StreamerUserBot

logger = logging.getLogger(__name__)


async def main():
    await StreamerUserBot.start()
    await StreamerBot.start()
    await idle()


if __name__ == "__main__":
    try:
        StreamerBot.run(main())
    except KeyboardInterrupt:
        logger.error("KeyboardInterruption: Services Terminated!")
