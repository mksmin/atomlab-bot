# Здесь создаю функции запросов к БД

# Импорт библиотек

# Импорт функций из библиотек
from sqlalchemy import select
from sqlalchemy import func

# Импорт из файлов
from app.database.models import async_session
from app.database.models import User, ChatUsers, Chat, Admin


# Функция обращается к БД и проверяет связь пользователя и чата в бд
async def set_user_chat(tg_id, chat_id, chat_title):
    async with async_session() as session:
        user = await session.scalar(select(ChatUsers).where(ChatUsers.tg_id == tg_id, ChatUsers.chat_id == chat_id))

        if not user:
            session.add(ChatUsers(tg_id=tg_id, chat_id=chat_id, chat_title=chat_title))
            await session.commit() # сохраняем информацию
        else:
            pass

        count_value = await session.scalar(select(func.count()).select_from(ChatUsers).where(ChatUsers.tg_id == tg_id))

        if count_value <=1:
            return True
        else:
            return False


# Используем контекстный менеджер, чтобы сессия закрывалась после исполнения функции
async def set_user(tg_id, username):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id, tg_username=username))
            await session.commit()  # сохраняем информацию


async def set_chat(chat_id, chat_title):
    async with async_session() as session:
        chat = await session.scalar(select(Chat).where(Chat.chat_id == chat_id))

        if not chat:
            print(chat_id)
            session.add(Chat(chat_id=chat_id, chat_title=chat_title))
            await session.commit()  # сохраняем информацию


async def get_chats(tg_id):  # Получаю список чатов, в которые вступил конкретный пользователь
    async with async_session() as session:
        data = await session.execute(select(ChatUsers.chat_title).where(ChatUsers.tg_id == tg_id))
        data_fetch = data.fetchall()
        data_list = []
        index = 0
        while index < len(data_fetch):
            first_strip = str(data_fetch[index]).strip("()")
            second_strip = f'— {first_strip.strip(",'")}'
            data_list.append(second_strip)
            index += 1
        data_return = '\n'.join(map(str, data_list))
        return data_return


async def get_list_chats():  # Получаю список id всех чатов из БД
    async with async_session() as session:
        data = await session.execute(select(Chat.chat_id))
        data_fetch = data.fetchall()

        data_list = []
        index = 0
        while index < len(data_fetch):
            first_strip = str(data_fetch[index]).strip("()")
            second_strip = first_strip.strip(",'")
            data_list.append(second_strip)
            index += 1

        return data_list


async def reg_admin(tg_id, username, first_name):
    async with async_session() as session:
        admin = await session.scalar(select(Admin).where(Admin.tg_id == tg_id))
        if not admin:
            session.add(Admin(tg_id=tg_id, username=username, first_name=first_name))
            await session.commit()


async def check_chat(chat_id, tg_id):  #
    return chat_id == tg_id
