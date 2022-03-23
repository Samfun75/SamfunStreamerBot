# Samfun Streamer Bot

This is a simple telegram bot to manage rtmps livestreams of telegram groups and channels.

## Requirments

- Pyrogram [View](https://github.com/pyrogram/pyrogram) - Telegram Client
- Pymongo - Mongodb for python
- FFmpeg - Audio/Video processor
- python-ffmpeg [View](https://github.com/jonghwanhyeon/python-ffmpeg) - FFmpeg python wrapper

## Installation

### Heroku

<br>

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/Samfun75/SamfunStreamerBot)

<br>

### Other systems

<br>

**Clone repository**

```bash
git clone https://github.com/Samfun75/SamfunStreamerBot
```

**Install FFmpeg**

Go to [FFmpeg.org](https://ffmpeg.org/download.html)

- For Windows install builds from gyan.dev
- For Linux and Mac install the static builds

**Change to repository directory**

```bash
cd SamfunStreamerBot
```

**Install requirements and dependencies**

```python
pip3 install -r requirements.txt
```

**Create `config.ini`**

Using the sample available at `streamer/working_dir/config.ini.sample` create `streamer/working_dir/config.ini`.

```ini
# Here is a sample of config file and what it should include:

# More info on API_ID and API_HASH can be found here: https://docs.pyrogram.org/intro/setup#api-keys

[pyrogram]
api_id = 1234567
api_hash = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
app_version = 1.0
device_model = PC
system_version = Windows

# Where pyrogram plugins are located

[plugins]
root = streamer/telegram/plugins


# More info on Bot API Key/token can be found here: https://core.telegram.org/bots#6-botfather

[bot-configuration]
bot_token = 123456789:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
user_session = BADGIDHwLxMhh8_q9xxxxxxxxxxxxxxxxxxxx # A user session string run the example here and input the result: https://docs.pyrogram.org/api/methods/export_session_string
session = StreamerBot
dustbin = -100xxxxxxxxx # Used to store uploaded book. id of a channel where the bot is admin
allowed_users = [123456789, 987654321] # Telegram id of users allowed to use the bot. If the bot is open to all put empty array like this []

# Mongodb Credentials

[database]
db_host = xxxxxxxxxx.xxxxx.mongodb.net or localhost # In this section db_host is the address of the machine where the MongoDB is running, with port number
db_username = username
db_password = password
db_name = BookdlBot
db_type = Mongo_Atlas (or Mongo_Community)

```

**Run bot with:**

`python -m streamer`

stop with <kbd>CTRL</kbd>+<kbd>C</kbd>

## Usage

- Send /start to start the bot
- Send /help to see all the available commands

Note: bot only works in private mode

## Known Issue

When bot is closed it might raise `ValueError: I/O operation on closed pipe asyncio` or `BrokenPipeError: [WinError 109] The pipe has been ended` or both for every livestream created and terminated. This only happens on Windows 10 afaik in my reseach. I don't think it happens to other systems but if I confirm othewise, I'll update the readme.

Although this does not affect the bots functionality, it is pretty annoying when the log is flooded. **If anyone know how to fix that issue or even silence it please open a PR.**

## TODO

- Allow selected users to act as user_session. Meaning they can auto create livestreams on user_session owned chats
- Add a 1 min(customizable) stream of channel image(or bot image) to give viewers to join the stream without missing the opening and circumvent a cut in the video because of telegram delay
- Add playlist mode using Queue
- Add scheduled streaming
