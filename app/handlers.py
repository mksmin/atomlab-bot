
# Импорт функций из библиотек
from aiogram import Router, F
from aiogram.filters import CommandStart, Command, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import Message, ContentType, ChatMemberUpdated, FSInputFile

# Импорт из файлов
from app.middlewares import RootProtect
import app.database.request as rq
from app.adminpanel import get_id_chat_root
from app.user_requests import get_time


router = Router() # обработчик хэндлеров

@router.message(CommandStart()) # Стартовый хэндлер
async def get_start(message: Message):
    from_user = message.from_user
    await rq.set_user(from_user.id, from_user.username)
    await message.answer(text=f'Привет, {from_user.first_name}!')


# Временная команда, которая регистрирует пользователя в бд
@router.message(Command('addme'))
async def get_member(message: Message):
    chat = message.chat
    from_user = message.from_user
    message_text = f'Добавил в бд'

    await rq.set_user(from_user.id, from_user.username)

    if chat.title:
        await rq.set_user_chat(from_user.id, message.chat.id, message.chat.title)

    await message.answer(message_text)

# Добавляем пользователя в бд после вступления
@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def get_member(update: ChatMemberUpdated):
    chat = update.chat
    from_user = update.from_user
    status = await rq.set_user_chat(from_user.id, chat.id, chat.title)

    match status:
        case True:
            message_text = f'Привет, {from_user.first_name}!'
            await update.answer(message_text)

        case False:
            if from_user.username == None:
                username_ = f'{from_user.first_name}'
            else:
                username_ = f'{from_user.first_name} (@{from_user.username})'

            message_text = (f'Привет, {username_}!\n'
                            f'Учиться можно только на одном направлении\n\n'
                            f'Я отправил админу сообщение, он свяжется с тобой и удалит тебя из других чатов')
            await update.answer(message_text)

            root_id = await get_id_chat_root()
            data_ = await rq.get_chats(update.from_user.id)
            await update.bot.send_message(chat_id=int(root_id),
                                           text=f'{username_}'
                                                f'\nвступил в несколько чатов: '
                                                f'\n\n{data_}'
                                                f'\n\nСвяжись с ним, чтобы обсудить детали')


@router.message(Command('timing')) #Функция получения расписания
async def get_timing(message: Message):
    if message.from_user.id == message.chat.id:
        await message.answer('Расписание можно получить только через чат компетенции')
    else:
        result = await get_time(message.chat.title)
        await message.answer(result, parse_mode='HTML')
