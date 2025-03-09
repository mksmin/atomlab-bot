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
import app.statesuser as st
from app.database import User, Project
from app.keyboards import keyboard_send_mess, cancel_key_prj, keys_for_create_project, rpanel, manage_projects, \
    confirm_deletion
from app.middlewares import ChatType, RootProtect
from config.config import get_id_chat_root, logger
from app.messages import msg_texts as mt
from app.handlers import get_user_profile

adm_r = Router()  # main handler
adm_r.my_chat_member.filter(F.chat.type.in_({'group', 'supergroup'}))


@adm_r.message(Command('my'), RootProtect())
async def get_panel(message: Message) -> None:
    """
    func for call root panel
    """
    text_for_message = (f'Ты вызвал панель владельца\n\n'
                        f'Твой ID: <code>{message.from_user.id}</code>\n'
                        f'ID чата: <code>{message.chat.id}</code>')
    await message.answer(text_for_message, reply_markup=rpanel)


@adm_r.message(Command('chatid'), RootProtect())
async def get_chat_id(message: Message) -> None:
    """
    func get chatid of where root-user used the command
    and sends it to the private chat of the root-user
    """
    root_id = await get_id_chat_root()
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
    await update.bot.send_message(chat_id=root_id,
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
@adm_r.message(Command('send'), RootProtect(), ChatType(chat_type='private'))
async def sendchats(message: Message | CallbackQuery, state: FSMContext):
    await state.set_state(st.Send.sendmess)  # Состояние ожидания сообщения

    if isinstance(message, CallbackQuery):
        message = message.message

    await message.answer(text=mt.start_message_for_func_sendchats)


@adm_r.message(st.Send.sendmess, RootProtect(), ChatType(chat_type='private'))
async def confirm(message: Message, state: FSMContext):
    await state.update_data(sendmess=message.html_text)

    if message.media_group_id:
        print('Это группа сообщений')
        print(f'{message.media_group_id = }')

    if message.photo:
        await state.set_state(st.Send.ph_true)
        await state.update_data(ph_true=message.photo[-1].file_id)
    else:
        await state.update_data(ph_true=None)

    data = await state.get_data()
    await message.answer(text='Вот так будет выглядеть твое сообщение:')
    if data['ph_true'] != None:
        await message.bot.send_photo(chat_id=message.chat.id, photo=data['ph_true'], caption=data['sendmess'])
    else:
        await message.answer(text=data['sendmess'])

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
async def get_statistic(message: Message | CallbackQuery):
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

    message = message.message if isinstance(message, CallbackQuery) else message

    with open(path_file, 'r') as f:
        data = json.load(f)
        token = data['Token']
        result_statistic = await get_stat('https://api.атом-лаб.рф/statistics/', token)
        message_to_send = await create_message_for_statistics(result_statistic)
        await message.answer(message_to_send)


@adm_r.message(Command('setadmin'), RootProtect(), ChatType(chat_type='private'))
async def set_admin(message: Message | CallbackQuery, state: FSMContext):
    message = message.message if isinstance(message, CallbackQuery) else message

    await state.set_state(st.Admins.admins)
    await message.answer('Пришли id пользователя, которого хочешь назначить администратором')


@adm_r.message(st.Admins.admins, RootProtect(), ChatType(chat_type='private'))
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


async def delete_keyboard_from_message(message: Message, state: FSMContext):
    """
    Удаляем кнопки отмены от предыдущиих сообщений, если пользователь на них не нажал, а отправил ответ
    :param message:
    :param state:
    :return:
    """

    data = await state.get_data()
    last_message_id = data.get("last_message_id")

    if last_message_id:
        try:
            # Удаляем клавиатуру из предыдущего сообщения
            await message.bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=last_message_id,
                reply_markup=None  # Убираем клавиатуру
            )
        except Exception as e:
            logger.warning(f"Ошибка при редактировании кнопок: {e}")


@adm_r.message(Command('help'), RootProtect())
async def help_for_admin(message: Message):
    await message.answer(text=mt.text_for_help_admin)


@adm_r.message(Command('create'), RootProtect(), ChatType(chat_type='private'))
async def create_project(message: Message, state: FSMContext):
    await state.set_state(st.ProjectState.prj_name)

    sent_message = await message.answer(mt.create_project, reply_markup=cancel_key_prj)
    await state.update_data(last_message_id=sent_message.message_id)


@adm_r.message(st.ProjectState.prj_name,
               RootProtect(),
               ChatType(chat_type='private'))
async def save_name_of_project(message: Message, state: FSMContext):
    await delete_keyboard_from_message(message, state)

    await state.update_data(prj_name=message.text, prj_owner=message.from_user.id)
    await state.set_state(st.ProjectState.prj_description)

    sent_message = await message.answer(mt.create_description_of_project, reply_markup=cancel_key_prj)
    await state.update_data(last_message_id=sent_message.message_id)


@adm_r.message(st.ProjectState.prj_description,
               RootProtect(),
               ChatType(chat_type='private'))
async def save_description_of_project(message: Message, state: FSMContext):
    await delete_keyboard_from_message(message, state)

    await state.update_data(prj_description=message.text)
    await message.answer(mt.succes_create_project)
    data = await state.get_data()

    user_project = Project(
        prj_name=data['prj_name'],
        prj_description=data['prj_description']
    )
    await message.answer(
        text=f'<b>Название проекта: </b>\n{user_project.prj_name}\n\n'
             f'<b>Описание проекта: </b>\n{user_project.prj_description}\n\n'
    )
    await message.answer('Сохранить проект?', reply_markup=keys_for_create_project)


@adm_r.callback_query(F.data == 'cancel_prj', RootProtect())
async def cancel_prj(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Ты решил не сохранять проект', reply_markup=None)
    await callback.answer('Операция отменена')
    await state.clear()


@adm_r.callback_query(F.data == 'save_prj', RootProtect())
async def save_prj(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_project = Project(
        prj_name=data['prj_name'],
        prj_description=data['prj_description'],
        prj_owner=data['prj_owner']
    )
    result = await rq.create_project_of_user(project=user_project)
    if result:
        await callback.message.edit_text('Проект успешно сохранен', reply_markup=None)
        await callback.answer('Проект успешно сохранен ')
        await state.clear()
    else:
        await callback.message.edit_text('Проект c таким названием уже существует ', reply_markup=None)
        await callback.answer('Проект не сохранен')
        await state.clear()


@adm_r.callback_query(F.data == 'myprojects', RootProtect())
async def save_prj(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Вызов списка проектов')

    list_projects_objects = await rq.get_list_of_projects(tg_user_id=callback.from_user.id)
    data_list = [result[0].prj_name for result in list_projects_objects]

    if len(data_list) > 0:
        list_of_names = '\n'.join(f'{i}. {item}' for i, item in enumerate(data_list, start=1))

        msg_text = (f'Вот твои проекты:\n'
                    f'{list_of_names}')
        inline_buttons = manage_projects

    else:
        msg_text = 'У тебя нет проектов'
        inline_buttons = None

    await callback.message.answer(text=msg_text, reply_markup=inline_buttons)


@adm_r.callback_query(F.data == 'create_prj', RootProtect())
async def create_prj_through_button(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Создаем проект')
    await create_project(message=callback.message, state=state)


@adm_r.callback_query(F.data == 'send_msg_fchats', RootProtect())
async def create_prj_through_button(callback: CallbackQuery, state: FSMContext):
    await callback.answer('В процессе... ')
    await sendchats(message=callback, state=state)


@adm_r.callback_query(F.data == 'user_profile', RootProtect())
async def admin_call_user_profile(callback: CallbackQuery):
    await callback.answer('В процессе... ')
    await get_user_profile(message=callback)


@adm_r.callback_query(F.data == 'set_user_to_admin', RootProtect())
async def admin_call_user_profile(callback: CallbackQuery, state: FSMContext):
    await callback.answer('В процессе... ')
    await set_admin(message=callback, state=state)


@adm_r.callback_query(F.data == 'get_statistics', RootProtect())
async def admin_call_user_profile(callback: CallbackQuery):
    await callback.answer('В процессе... ')
    await get_statistic(message=callback)


@adm_r.callback_query(F.data == 'delete_project', RootProtect())
async def admin_init_remove_project(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Будем удалять проект')
    await state.set_state(st.DeleteEntry.object_number)
    await callback.message.answer(f'Пришли номер проекта, который хочешь удалить')


@adm_r.message(F.text.regexp(r"^\d+$"),
               st.DeleteEntry.object_number,
               ChatType(chat_type='private'),
               RootProtect())
async def get_number_of_project(message: Message, state: FSMContext):
    list_projects_objects = await rq.get_list_of_projects(tg_user_id=message.from_user.id)
    data_list = [result[0] for result in list_projects_objects]

    if len(data_list) < 1:
        await message.answer(f'Возникла ошибка. Не нашел активных проектов. Операция отменена ')
        await state.clear()
        return

    index_looking_for = int(message.text) - 1

    if index_looking_for > len(data_list) - 1:
        await message.answer(f'Ошибка. Отправь число от 1 до {len(data_list)}')
        return

    project_to_delete: Project = data_list[index_looking_for]

    sent_message = await message.answer(f'Подтвердить удаление проекта <b>{project_to_delete.prj_name}?</b>',
                                        reply_markup=confirm_deletion)
    await state.update_data(object_number=project_to_delete, last_message_id=sent_message.message_id)


@adm_r.callback_query(F.data == 'confirm_delete', RootProtect())
async def admin_confirm_delete_prj(callback: CallbackQuery, state: FSMContext):
    # Получаю конкретный объект класса Project для удаления
    data = await state.get_data()
    project_to_delete = data['object_number']

    try:
        await rq.delete_entry(obj=project_to_delete)
        await callback.answer(f'Удален успешно')
        await callback.message.edit_text(f'Проект успешно удален', reply_markup=None)
        await state.clear()
        return

    except Exception as e:
        await callback.message.edit_text(f'Операция отменена. Возникла ошибка: {e}', reply_markup=None)
        await callback.answer(f'Ошибка при удалении')
        await state.clear()
        return


@adm_r.message(st.DeleteEntry.object_number, RootProtect(), ChatType(chat_type='private'))
async def get_nuber_of_project(message: Message):
    await message.answer(f'Ты прислал не число')


@adm_r.callback_query(F.data == 'cancel_delete', RootProtect())
async def admin_cancel_delete(callback: CallbackQuery, state: FSMContext):
    await callback.answer(f'Операция отменена')
    await callback.message.edit_text(f'Ты решил не удалять проект', reply_markup=None)
    await state.clear()
    return

@adm_r.callback_query(F.data == 'checkout_project', RootProtect())
async def admin_cancel_delete(callback: CallbackQuery, state: FSMContext):
    await callback.answer(f'Пока ничего нет')
    await state.clear()
    return
