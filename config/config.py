"""
this module load environment and read .env file
"""
# import libraries
import logging
import os

# import from libraries
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


async def get_id_chat_root() -> int:
    """
    :return: id of root-chat as str
    """
    return int(settings.bot.root_chat)


class BotConfig(BaseModel):
    token: str
    root: int
    root_chat: int


class DatabaseConfig(BaseModel):
    url: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(Path(__file__).parent / ".env.template", Path(__file__).parent / ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
        env_file_encoding="utf-8"
    )
    bot: BotConfig
    db: DatabaseConfig


settings = Settings()
