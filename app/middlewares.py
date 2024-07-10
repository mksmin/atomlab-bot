# Делаю фильтры и middlewares
import asyncio
from typing import Union

from aiogram.filters import Filter
from aiogram.types import Message
from config.config import get_tokens


async def get_id_root():
    root_id = await get_tokens("ROOT")
    return root_id


class RootProtect(Filter):
    async def __call__(self, message: Message):
        root_id = await get_id_root()
        return str(message.from_user.id) in root_id


# Класс для фильтрации обращения к боту
# Использовать private или group and supergroup
class CheckChatBot(Filter):
    def __init__(self, chat_type: Union[str, list]):
        self.chat_type = chat_type

    async def __call__(self, message: Message) -> bool:
        if isinstance(self.chat_type, str):
            return message.chat.type == self.chat_type
        else:
            return message.chat.type in self.chat_type
