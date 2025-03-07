"""
This module for filtering and middlewares
"""

# import from libraries
from aiogram.filters import Filter
from aiogram.types import Message

# import from modules
from config.config import get_tokens
from app.database import get_one_user_by_tgid, User
from app.database.models import async_session


class RootProtect(Filter):
    """
    The class for filtering decorator
    accept user's id, return True if id is root-user
    """
    async def __call__(self, message: Message) -> bool:
        async with async_session() as session:
            user: User = await get_one_user_by_tgid(session=session, tg_id=message.from_user.id)
        access_status = ('owner',)
        return user.user_status in access_status


class ChatType(Filter):
    """
    The class for filtering decorator
    waiting for type of chat in private, group or supergroup
    """

    def __init__(self, chat_type: str | list):
        self.chat_type = chat_type

    async def __call__(self, message: Message) -> bool:
        if isinstance(self.chat_type, str):
            return message.chat.type == self.chat_type
        else:
            return message.chat.type in self.chat_type
