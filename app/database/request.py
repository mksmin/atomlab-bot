"""
Module with functions for requesting data from database
"""

# import libraries

# import from libraries
from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy.sql import text

# import from modules
from app.database.models import async_session
from app.database.models import User, ChatUsers, Chat


async def set_user_chat(tg_id, chat_id) -> int:
    """
    Function for writing a user and chat, where he's member, to database

    Function doing request to database and checkout link User and Chat
    If there is no record, then create it
    If user is a member in two chats or more

    :param tg_id: (int) id of the user from telegram
    :param chat_id: (int) id of the chat from telegram
    :return: (int) count chat where user is member
    """

    async with async_session() as session:
        is_private_chat = (tg_id == chat_id)  # Фильтр, чтобы в базу не добавлялся чат пользователя с ботом
        # Check if there is an entry in database:
        user_in_db = await session.scalar(
            select(ChatUsers).where(ChatUsers.tg_id == tg_id,
                                    ChatUsers.chat_id == chat_id))

        if not user_in_db and not is_private_chat:
            session.add(ChatUsers(tg_id=tg_id, chat_id=chat_id))
            await session.commit()  # save

        # Надо проверить, что будет, если записи не будет -- вернет ли 0 или None
        count_value = await session.scalar(select(func.count()).select_from(ChatUsers).where(ChatUsers.tg_id == tg_id))
        return count_value


async def set_user(tg_id, username: str = 'Null') -> None:
    """
    Function for writing a user to database

    :param tg_id: (int) id of the user from telegram
    :param username: (str) username of the user from telegram
    :return: None
    """

    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id, tg_username=username))
            await session.commit()  # сохраняем информацию


async def set_chat(chat_id, chat_title) -> None:
    """
    Function for writing a chat to database
    :param chat_id: (int) id of the chat from telegram
    :param chat_title: (str) title of the chat from telegram
    :return: None
    """

    async with async_session() as session:
        chat = await session.scalar(select(Chat).where(Chat.chat_id == chat_id))

        if not chat:
            session.add(Chat(chat_id=chat_id, chat_title=chat_title))
            await session.commit()  # save


async def get_chats(tg_id) -> str:
    """
    Function for read database and get list of chats, where user is member
    :param tg_id: (int) id of the user from telegram
    :return: (str) list of chats as str
    """
    # Получаю список чатов, в которые вступил конкретный пользователь
    async with async_session() as session:
        request_to_sql = select(Chat.chat_title).select_from(Chat)
        request_with_join = request_to_sql.join(ChatUsers, ChatUsers.chat_id == Chat.chat_id)
        request_with_filter = request_with_join.where(ChatUsers.tg_id == tg_id)
        data_from_db = await session.execute(request_with_filter)

        chats_titles_list = data_from_db.fetchall()
        data_list = []
        for name in chats_titles_list:
            first_strip = str(name).strip("()")
            second_strip = f'— {first_strip.strip(",'")}'
            data_list.append(second_strip)
        data_return = '\n'.join(map(str, data_list))
        return data_return


async def get_list_chats() -> list:  # Получаю список id всех чатов из БД
    """
    Function for read database and get list of all chats
    :return: (List[int]: [-123, -456]) list with id of chats
    """
    async with async_session() as session:
        data = await session.execute(select(Chat.chat_id))
        data_fetch = data.fetchall()  # return 'sqlalchemy.engine.row.Row' as [(-123,), (-456,)]

        data_list = []
        for element in data_fetch:
            first_strip = str(element).strip("()")
            second_strip = first_strip.strip(",")
            data_list.append(int(second_strip))

        return data_list


# Работа с репутацией
# Функция обращается к БД и выгружает значение очков репутации
async def check_karma(tg_id_sender, tg_id_recipient):
    async with async_session() as session:
        sender = await session.scalar(select(User).where(User.tg_id == tg_id_sender))
        recipient = await session.scalar(select(User).where(User.tg_id == tg_id_recipient))

        if not recipient:
            await set_user(tg_id_recipient)
        if not sender:
            await set_user(tg_id_sender)

        text_recipient = text(f"SELECT tg_id, total_karma FROM users WHERE tg_id = {tg_id_recipient}")
        text_sender = text(f"SELECT tg_id, karma_start_value FROM users WHERE tg_id = {tg_id_sender}")
        karma_sender = await session.execute(text_sender)
        karma_recipient = await session.execute(text_recipient)
        await session.commit()
        return karma_sender, karma_recipient


# Функция обновляет репутацию пользователя и уменьшает очки репутации у отправителя
async def update_karma(id_send, send_new_karma,
                       recipient_id, recipient_new_karma) -> None:
    async with async_session() as session:
        s = await session.scalar(select(User).where(User.tg_id == id_send))
        s.karma_start_value = int(send_new_karma)
        r = await session.scalar(select(User).where(User.tg_id == recipient_id))
        r.total_karma = int(recipient_new_karma)
        session.add(s, r)
        await session.commit()
