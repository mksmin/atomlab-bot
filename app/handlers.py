# Импорт функций из библиотек
from aiogram import Router, F
from aiogram.filters import CommandStart, Command, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER, ADMINISTRATOR, KICKED, LEFT, RESTRICTED, MEMBER, CREATOR
from aiogram.types import Message, ContentType, ChatMemberUpdated, FSInputFile

# Импорт из файлов
from app.middlewares import CheckChatBot
import app.database.request as rq
from app.adminpanel import get_id_chat_root
from app.user_requests import get_time

router = Router()  # обработчик хэндлеров


@router.message(CommandStart())  # Стартовый хэндлер
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


# Добавляем пользователя в бд после вступления в чат
@router.chat_member(ChatMemberUpdatedFilter(
    member_status_changed=
    (KICKED | LEFT | -RESTRICTED)
    >>
    (+RESTRICTED | MEMBER)
))
async def get_member(update: ChatMemberUpdated):
    chat = update.chat
    from_user = update.new_chat_member.user
    status = await rq.set_user_chat(from_user.id, chat.id, chat.title)
    await rq.set_user(from_user.id, from_user.username)

    match status:
        case True:
            message_text = f'Привет, {from_user.first_name}!'
            await update.answer(message_text)

        case False:
            if from_user.username is None:
                username_ = f'{from_user.first_name}'
            else:
                username_ = f'{from_user.first_name} (@{from_user.username})'

            message_text = (f'Привет, {from_user.username}!\n'
                            f'Учиться можно только на одном направлении\n\n'
                            f'Я отправил админу сообщение, он свяжется с тобой и удалит тебя из других чатов')
            await update.answer(message_text)

            root_id = await get_id_chat_root()
            data_ = await rq.get_chats(from_user.id)
            await update.bot.send_message(chat_id=int(root_id),
                                          text=f'{username_}'
                                               f'\nвступил в несколько чатов: '
                                               f'\n\n{data_}'
                                               f'\n\nСвяжись с ним, чтобы обсудить детали')


# /-- timing start --/
# Функция получения расписания через чат компетенции
@router.message(Command('timing'), CheckChatBot(chat_type=["group", "supergroup"]))
async def get_timing(message: Message):
    result = await get_time(message.chat.title)
    await message.answer(result, parse_mode='HTML')


# Фильтрует, если в бота написать
# Понадобится потом для доп функционала
@router.message(Command('timing'), CheckChatBot(chat_type="private"))
async def get_timing(message: Message):
    await message.answer('Расписание можно получить только через чат компетенции')


# /-- timing end--/


# /-- karma start --/
# Функция увеличения репутации за помощь
@router.message(F.reply_to_message,
                F.text.lower().contains('+rep'),
                CheckChatBot(chat_type=["group", "supergroup"]))
async def add_rep(message: Message):
    id_recipient = message.reply_to_message.from_user.id
    id_sender = message.from_user.id
    if id_recipient == message.bot.id:
        await message.reply(f'Боту нельзя поднять репутацию, но спасибо, что ты ценишь его работу')

    elif id_recipient == id_sender:
        await message.reply(f'Самому себе нельзя поднять репутацию')

    else:
        result = await rq.check_karma(id_sender, id_recipient)
        dict_value = {
            'send': '',
            'recipitent': '',
        }

        for ind in range(2):
            for i, v in result[ind]:
                dict_new = {
                    'ID': i,
                    'karma': v
                }
                index = list(dict_value.keys())
                dict_value.update({
                    index[ind]: dict_new
                })
        else:
            dict_value['send']['karma'] = str(int(dict_value['send']['karma']) - 1)
            if int(dict_value['send']['karma']) < 0:
                await message.reply(f'Упс! У тебя закончились очки репутации')
            else:
                send_id, send_karma = dict_value['send']['ID'], dict_value['send']['karma']
                recip_id, recip_karma = dict_value['recipitent']['ID'], dict_value['recipitent']['karma']
                dict_value['recipitent']['karma'] = str(int(recip_karma) + 1)
                await rq.update_karma(send_id, send_karma,
                                      recip_id, recip_karma)
                await message.reply(f'Репутация @{message.reply_to_message.from_user.username} повышена. '
                                    f'У тебя осталось очков репутации - <b>{dict_value['send']['karma']}</b>'
                                    f'\n\nУзнать какая репутация - нельзя')

# /-- karma end --/
