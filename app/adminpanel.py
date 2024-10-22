# import libraries
import aiohttp
import json
import os

# import functions from libraries
from aiogram import F, Router
from aiogram.filters import ADMINISTRATOR, Command, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import CallbackQuery, ChatMemberUpdated, Message
from aiogram.fsm.context import FSMContext

# import functions from my modules
import app.database.request as rq
from app.keyboards import keyboard_send_mess
from app.middlewares import CheckChatBot, RootProtect
from app.statesuser import Send, Admins
from config.config import get_id_chat_root, logger

adm_r = Router()  # main handler
adm_r.my_chat_member.filter(F.chat.type.in_({'group', 'supergroup'}))


@adm_r.message(Command('rpanel'), RootProtect())
async def get_panel(message: Message) -> None:
    """
    func for call root panel
    """
    text_for_message = (f'Ты вызвал панель владельца\n\n'
                        f'Твой ID: {message.from_user.id}\n'
                        f'ID чата: {message.chat.id}')
    await message.answer(text_for_message)


@adm_r.message(Command('chatid'), RootProtect())
async def get_chat_id(message: Message) -> None:
    """
    func get chatid of where root-user used the command
    and sends it to the private chat of the root-user
    """
    root_id = int(await get_id_chat_root())
    await message.bot.send_message(chat_id=root_id,
                                   text=f'Ты запросил ID чата\n\n'
                                        f'Чат id - {message.chat.id}\n'
                                        f'Название: {message.chat.title}')


# manual register chat by root-user
@adm_r.message(Command('addchat'), RootProtect())
async def register_chat_to_db(message: Message) -> None:
    chat_id = message.chat.id
    chat_title = message.chat.title
    await rq.set_chat(chat_id, chat_title)


# Регистрируем чат в БД после добавления бота администратором
@adm_r.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=(IS_NOT_MEMBER | IS_MEMBER) >> ADMINISTRATOR
    )
)
async def bot_added_as_admin(update: ChatMemberUpdated):
    root_id = await get_id_chat_root()
    await update.bot.send_message(chat_id=int(root_id),
                                  text=f'Бот стал администратором группы'
                                       f'\n\n<b>Название группы:</b>'
                                       f'\n{update.chat.title}'
                                       f'\n<b>ID группы:</b> {update.chat.id}'
                                       f'\n<b>Тип группы:</b> {update.chat.type}')
    chat_id = update.chat.id
    chat_title = update.chat.title
    await rq.set_chat(chat_id, chat_title)


# /-- send start--/

# Функция отправки сообщения во все чаты
# Умеет отлавливать фото с тектом или только текст (форматированный)
# Не умеет работать с остальным контентом
@adm_r.message(Command('send'), RootProtect(), CheckChatBot(chat_type='private'))
async def sendchats(message: Message, state: FSMContext):
    await state.set_state(Send.sendmess)  # Состояние ожидания сообщения
    await message.answer(f'Пришли сообщение для отправки'
                         f'\n\nЭто может быть фотография с описанием '
                         f'или форматированный текст'
                         f'\n\nДругой контент отправлять пока не умею')


@adm_r.message(Send.sendmess, RootProtect(), CheckChatBot(chat_type='private'))
async def confirm(message: Message, state: FSMContext):
    await state.update_data(sendmess=message.html_text)

    if message.media_group_id:
        print('Это группа сообщений')
        print(f'{message.media_group_id = }')

    if message.photo:
        await state.set_state(Send.ph_true)
        await state.update_data(ph_true=message.photo[-1].file_id)
    else:
        await state.update_data(ph_true=None)

    await message.answer('Отправляем?', reply_markup=keyboard_send_mess)


@adm_r.callback_query(F.data == 'send', RootProtect())
async def send_message(callback: CallbackQuery, state: FSMContext):
    message = callback.bot
    error_msg = []

    await callback.answer('Запустил отправку')
    data = await state.get_data()

    chat_id = await rq.get_list_chats()
    for chat in chat_id:
        chat_obj = chat[0]
        try:
            if data['ph_true']:
                await message.send_photo(chat_id=chat_obj.chat_id,
                                         photo=data['ph_true'],
                                         caption=data['sendmess'])
                continue
            await message.send_message(chat_id=chat_obj.chat_id,
                                       text=data['sendmess'])
        except Exception as err:
            error_msg.append(f'<b>{chat_obj.chat_title}</b> ({chat_obj.chat_id}): {str(err)}')
    else:
        if error_msg:
            list_error = '\n'.join(error_msg)
            message_to_send = (f'Возникли ошибки при отправке: \n\n'
                               f'{list_error}')
            await callback.message.edit_text(message_to_send, reply_markup=None)
        else:
            await callback.message.edit_text('Все сообщения отправлены', reply_markup=None)

    await state.clear()


@adm_r.callback_query(F.data == 'cancel', RootProtect())
async def cancel_send(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Ты решил не отправлять сообщение', reply_markup=None)
    await callback.answer('Операция отменена')
    await state.clear()


# /-- send end--/


# Временная функция для проверки (удалить после использования)
@adm_r.message(Command('checkme'), RootProtect())
async def tmp_check_me_in_db(message: Message):
    from_user = message.from_user
    status = await rq.set_user_chat(message.from_user.id, message.chat.id)
    data_ = await rq.get_chats(message.from_user.id)
    await message.answer(text=f'чаты: {data_}\n'
                              f'значение - {status}')
    match status:
        case True:
            message_text = f'Привет, {from_user.first_name}!'
            await message.answer(message_text)

        case False:
            if from_user.username is None:
                username_ = f'{from_user.first_name}'
            else:
                username_ = f'{from_user.first_name} (@{from_user.username})'

            message_text = (f'Привет, {username_}!\n'
                            f'Учиться можно только на одном направлении\n\n'
                            f'Я отправил админу сообщение, он свяжется с тобой и удалит тебя из других чатов')
            await message.answer(message_text)


async def get_token(url: str, user_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{url}{user_id}') as resp:
            return await resp.json()


async def get_stat(url_r: str, token_r: int):
    headers = {"token": token_r}
    async with aiohttp.ClientSession() as session:
        async with session.get(url_r, headers=headers) as response:
            return await response.json()


async def validate_response_from_server(server_response: dict | str) -> dict:
    """
    Функция проверяет ответ от сервера. Если в ответе есть error, то возвращает текст ошибки,
    если нет, то возвращает исходный ответ\n
    Example error: server_response: {'message': {'error': 'invalid token'}}\n
    Example success: server_response: {'message': {'total_users': 0, 'details': {'name1': '123', 'name2': '123'}}}
    :param server_response: json str
    :return: dict with response
    """
    # Если отсутсвует token в headers -> вернет dict с ошибкой
    if isinstance(server_response, dict) and server_response.get('detail'):
        message_to_return = {'error': str(server_response.get('detail'))}
        return message_to_return

    data = json.loads(server_response)  # str to dict
    message_data = data['message']

    if message_data.get('error'):
        message_to_return = {'error': message_data.get('error')}
        return message_to_return

    return data


async def create_message_for_statistics(server_response: str) -> str:
    data = await validate_response_from_server(server_response)

    if data.get('error'):
        return data['error']

    list_ = []
    for name, value in data['message']['details'].items():
        list_.append(f'{name}: {value}')

    message = '\n'.join(list_)
    message_to_return = (f"<b>Статистика регистрации</b>\n"
                         f"Всего заявок: {data['message']['total_users']}"
                         f"\n\nДетально по компетенциям:"
                         f"\n{message}")
    return message_to_return


@adm_r.message(Command('getstat'), RootProtect())
async def get_statistic(message: Message):
    user_id = message.from_user.id

    path_dir = os.path.dirname(os.path.abspath(__file__))
    path_file = os.path.join(path_dir, f'auth/{user_id}.json')

    dir_exists = os.path.exists(os.path.join(path_dir, 'auth'))
    file_exists = os.path.exists(path_file)

    if not dir_exists:
        os.makedirs(os.path.join(path_dir, 'auth'))

    if not file_exists:
        result_token = await get_token('https://api.атом-лаб.рф/get_token/', user_id)
        with open(path_file, 'x') as f:
            token = result_token['message']
            message_to_write = {"User": user_id, "Token": token}
            json.dump(message_to_write, f)

    with open(path_file, 'r') as f:
        data = json.load(f)
        token = data['Token']
        result_statistic = await get_stat('https://api.атом-лаб.рф/statistics/', token)
        message_to_send = await create_message_for_statistics(result_statistic)
        await message.answer(message_to_send)


@adm_r.message(Command('setadmin'), RootProtect(), CheckChatBot(chat_type='private'))
async def set_admin(message: Message, state: FSMContext):
    await state.set_state(Admins.admins)
    await message.answer('Пришли id пользователя, которого хочешь назначить администратором')


@adm_r.message(Admins.admins, RootProtect(), CheckChatBot(chat_type='private'))
async def set_admins(message: Message, state: FSMContext):
    type_of_errors = {
        'Telegram server says - Bad Request: not enough rights': 'Недостаточно прав',
        'Telegram server says - Bad Request: USER_NOT_MUTUAL_CONTACT': 'Пользователь не состоит в группе'
    }

    try:
        user_id = int(message.text)
    except TypeError as err:
        await message.answer(f'Ошибка. Нужно прислать число, а не {type(message.text)}')
        await state.clear()
        return None

    chat_ids = await rq.get_list_chats()
    errors_dict = {}
    for chat in chat_ids:
        chat_obj = chat[0]
        try:
            await message.bot.promote_chat_member(chat_obj.chat_id, user_id,
                                                  can_promote_members=True,
                                                  can_edit_messages=True,
                                                  can_delete_messages=True,
                                                  can_manage_chat=True,
                                                  can_change_info=True,
                                                  can_restrict_members=True,
                                                  can_invite_users=True,
                                                  can_pin_messages=True,
                                                  can_manage_video_chats=True
                                                  )
        except Exception as err:
            error = str(err)
            if not type_of_errors.get(error):
                errors_dict[chat_obj.chat_title] = 'Неизвестная ошибка'
                logger.warning(f'Ошибка с чатом {chat_obj.chat_title}: {error}')
                continue

            errors_dict[chat_obj.chat_title] = type_of_errors[error]
            continue

    if errors_dict:
        list_ = []
        for i, v in errors_dict.items():
            list_.append(f'{i}: {v}\n')
        await message.answer(f"Закончил. Вот ошибки: \n{''.join(list_)}")
    else:
        await message.answer('Закончил без ошибок')
    await state.clear()


# Временная команда, которая регистрирует пользователя в бд
# @adm_r.message(Command('addme'), RootProtect())
# async def tmp_get_member(message: Message):
#     from_user = message.from_user
#     message_text = f'Добавил в бд'
#
#     await rq.set_user(from_user.id, from_user.username)
#     count_chats = await rq.set_user_chat(from_user.id, message.chat.id)
#
#     if count_chats < 2:
#         await message.answer(message_text)
#     else:
#         message_text = f'ВНИМАНИЕ! Больше одного чата!'
#         await message.answer(message_text)
#         root_id = await get_id_chat_root()
#         data_ = await rq.get_chats(from_user.id)
#         await message.bot.send_message(chat_id=int(root_id),
#                                        text=f'{message.from_user.username}'
#                                             f'\nвступил в несколько чатов: '
#                                             f'\n\n{data_}'
#                                             f'\n\nСвяжись с ним, чтобы обсудить детали')
