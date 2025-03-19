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


async def get_tokens(name_of_token: str) -> str:
    """
    function accept name as str
    load .env file
    find token {name}

    :param name_of_token:
    :return: token as str
    """
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        return os.getenv(name_of_token)
    else:
        print("No .env file found")


async def get_id_chat_root() -> int:
    """
    :return: id of root-chat as str
    """
    root_tgid = await get_tokens("ROOT_CHAT")
    return int(root_tgid)


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

    # временные переменные, чтобы pydantic не ругался
    token: str
    postsql_host: str
    root: int
    root_chat: int
    postgresql_prod: str
    token_prod: str


settings = Settings()
