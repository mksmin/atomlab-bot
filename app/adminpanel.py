# Импорт функций из библиотек
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Импорт из файлов
from app.middlewares import RootProtect
from config.config import get_tokens
import app.database.request as rq
from app.database.models import drop_all
from app.statesuser import Send
from app.keyboards import keyboard_send_mess


adm_r = Router() # обработчик хэндлеров
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

@adm_r.message(Command('addchat'), RootProtect())
async def gaddchat_sql(message: Message):
    chat_id = message.chat.id
    chat_title = message.chat.title

    await rq.set_chat(chat_id, chat_title)

@adm_r.message(Command('dropall'), RootProtect())
async def gaddchat_sql(message: Message):
    await drop_all()

# Функция отправки сообщения во все чаты
@adm_r.message(Command('send'), RootProtect())
async def sendchats(message: Message, state: FSMContext):
    await state.set_state(Send.sendmess) # Состояние ожидания сообщения
    id = await rq.check_chat(message.chat.id, message.from_user.id)
    if id:
        await message.answer(f'Пришли сообщение для отправки')

    else:
        await message.answer(f'В чате это не работает, только в боте')
        await state.clear()


@adm_r.message(Send.sendmess, RootProtect())
async def confirm(message: Message, state: FSMContext):
    await state.update_data(sendmess=message.html_text)  # Сейчас отлавливает только текст, нужно еще картинку и ссылки
    if message.photo:
        await state.set_state(Send.ph_true)
        await state.update_data(ph_true=message.photo[-1].file_id)
    else:
        await state.update_data(ph_true='False')
        pass

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

# Конец функции отправки сообщений во все чаты
