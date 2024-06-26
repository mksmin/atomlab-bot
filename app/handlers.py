
# Импорт функций из библиотек

from aiogram import Router, F
from aiogram.filters import CommandStart, Command, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import Message, ContentType, ChatMemberUpdated

# Импорт из файлов
from app.middlewares import RootProtect
import app.database.request as rq
from app.adminpanel import get_id_chat_root



router = Router() # обработчик хэндлеров



@router.message(CommandStart()) # Стартовый хэндлер
async def get_start(message: Message):
    from_user = message.from_user
    await rq.set_user(from_user.id, from_user.username)


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
                username_ = ''
            else:
                username_ = f' (@{from_user.username})'

            message_text = (f'Привет, {from_user.first_name}{username_}!\n'
                            f'Учиться можно только на одном направлении\n\n'
                            f'Я отправил админу сообщение, он свяжется с тобой и удалит тебя из других чатов')
            await update.answer(message_text)

            root_id = await get_id_chat_root()
            data_ = await rq.get_chats(update.from_user.id)
            await update.bot.send_message(chat_id=int(root_id),
                                           text=f'{from_user.first_name} {username_}'
                                                f'\nвступил в несколько чатов: '
                                                f'\n\n{data_}'
                                                f'\n\nСвяжись с ним, чтобы обсудить детали')


# Временная функция для проверки (удалить после использования)
@router.message(Command('checkme'))
async def checkme(message: Message):
    status = await rq.set_user_chat(message.from_user.id, message.chat.id, message.chat.title)

    print(f'Получил значение {status}')
