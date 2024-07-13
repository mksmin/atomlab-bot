# Импорт функций из библиотек
from aiogram import Router, F
from aiogram.filters import Command, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER, ADMINISTRATOR
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, ChatMemberUpdated
from aiogram.fsm.context import FSMContext

# Импорт из файлов
from app.middlewares import RootProtect, CheckChatBot
from config.config import get_tokens
import app.database.request as rq
from app.database.models import drop_all
from app.statesuser import Send
from app.keyboards import keyboard_send_mess

adm_r = Router()  # обработчик хэндлеров
adm_r.my_chat_member.filter(F.chat.type.in_({'group', 'supergroup'}))

async def get_id_chat_root():
    return await get_tokens("ROOT_CHAT")


@adm_r.message(Command('rpanel'), RootProtect())
async def get_panel(message: Message):
    await message.answer(f'Ты вызвал панель владельца')


@adm_r.message(Command('chatid'), RootProtect())
async def get_chat_id(message: Message):
    root_id = await get_id_chat_root()
    await message.bot.send_message(chat_id=int(root_id),
                                   text=f'Ты запросил айди чата:\n'
                                        f'Чат id - {message.chat.id}\n'
                                        f'Название: {message.chat.title}')

# Регистрация чата вручную рутпользователем
@adm_r.message(Command('addchat'), RootProtect())
async def add_chat_sql(message: Message):
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



# Очищает БД
@adm_r.message(Command('dropall'), RootProtect())
async def rm_database_sheets():
    await drop_all()

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
    if message.photo:
        await state.set_state(Send.ph_true)
        await state.update_data(ph_true=message.photo[-1].file_id)
    else:
        await state.update_data(ph_true='False')

    await message.answer('Отправляем?', reply_markup=keyboard_send_mess)


@adm_r.callback_query(F.data == 'send', RootProtect())
async def send_message(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Запустил отправку')
    data = await state.get_data()
    chat_id = await rq.get_list_chats()
    if data['ph_true'] != 'False':
        for i in chat_id:
            await callback.bot.send_photo(chat_id=i, photo=data['ph_true'], caption=data['sendmess'])
    else:
        for i in chat_id:
            await callback.bot.send_message(chat_id=i, text=data['sendmess'])

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
async def checkme(message: Message):
    from_user = message.from_user
    status = await rq.set_user_chat(message.from_user.id, message.chat.id, message.chat.title)
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
