#Делаю фильтры и middlewares
import asyncio

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


class CheckChatBot(Filter): # Проверяет, что запрос делается в бота
    async def __call__(self, message: Message):
        tg_id = message.from_user.id
        chat_id = message.chat.id
        return tg_id == chat_id