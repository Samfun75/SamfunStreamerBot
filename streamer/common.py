import os
import ast
from pathlib import Path
import configparser


class Common:

    def __init__(self):
        """Common: are commonly shared variables across the application that is loaded from the config file or env."""
        self.working_dir = Path('streamer/working_dir')

        self.is_env = bool(os.environ.get("ENV", None))
        if self.is_env:
            self.user_session = os.environ.get("USER_SESSION", '')
            self.tg_api_id = int(os.environ.get("TG_API_ID"))
            self.tg_api_hash = os.environ.get("TG_API_HASH")
            self.bot_session = ":memory:"
            self.bot_api_token = os.environ.get("TG_BOT_TOKEN")
            self.allowed_users = ast.literal_eval(
                os.environ.get("ALLOWED_USERS", '[]'))
            self.db_host = os.environ.get("DATABASE_DB_HOST", None)
            self.db_username = os.environ.get("DATABASE_DB_USERNAME", None)
            self.db_password = os.environ.get("DATABASE_DB_PASSWORD", None)
            self.db_name = os.environ.get("DATABASE_DB_NAME",
                                          "SamfunStreamerBot")
            if os.environ.get("DATABASE_DB_TYPE",
                              None).lower().split('_')[1] == 'community':
                self.db_type = 'mongodb'
            else:
                self.db_type = 'mongodb+srv'
        else:
            self.app_config = configparser.ConfigParser()

            self.app_config_file = "streamer/working_dir/config.ini"
            self.app_config.read(self.app_config_file)

            self.user_session = self.app_config.get("bot-configuration",
                                                    "user_session",
                                                    fallback='')
            self.tg_api_id = int(self.app_config.get("pyrogram", "api_id"))
            self.tg_api_hash = self.app_config.get("pyrogram", "api_hash")
            self.bot_session = self.app_config.get("bot-configuration",
                                                   "session")
            self.bot_api_token = self.app_config.get("bot-configuration",
                                                     "bot_token")
            self.allowed_users = ast.literal_eval(
                self.app_config.get("bot-configuration",
                                    "allowed_users",
                                    fallback='[]'))
            self.convert_api = self.app_config.get("convert",
                                                   "convert_api",
                                                   fallback=None)
            self.db_host = self.app_config.get("database",
                                               "db_host",
                                               fallback=None)
            self.db_username = self.app_config.get("database",
                                                   "db_username",
                                                   fallback=None)
            self.db_password = self.app_config.get("database",
                                                   "db_password",
                                                   fallback=None)
            self.db_name = self.app_config.get("database",
                                               "db_name",
                                               fallback="SamfunStreamerBot")
            if self.app_config.get(
                    "database",
                    "db_type").lower().split('_')[1] == 'community':
                self.db_type = 'mongodb'
            else:
                self.db_type = 'mongodb+srv'
