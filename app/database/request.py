"""
Module with functions for requesting data from database
"""

# import from
from functools import wraps
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

# import from modules
from app.database.models import async_session, ChatUsers, Chat, User
from config import logger


def connection(function):
    """
    this decorator is used to make a database connection
    """

    @wraps(function)
    async def wrapper(*args, **kwargs):
        async with async_session() as session:
            return await function(session, *args, **kwargs)

    return wrapper


async def get_one_user_link_with_chat(session: async_session, user_id: int, chat_id: int) -> ChatUsers | None:
    """
    The function for getting ChatUser obj
    :param session: async database session from SQLAlchemy
    :param user_id: (int)
    :param chat_id: (int)
    :return: ChatUsers's obj if it's exist, or None if it doesn't exist
    """
    result = await session.scalar(select(ChatUsers).where(ChatUsers.tg_id == user_id,
                                                          ChatUsers.chat_id == chat_id))
    return result


async def get_one_user_by_tgid(session: async_session, tg_id: int) -> User | None:
    user = await session.scalar(select(User).where(User.tg_id == tg_id))
    return user


@connection
async def set_user_chat(session: async_session, tg_id, chat_id) -> None:
    """
    Function for writing a user and chat, where he's member, to database

    Function doing request to database and checkout link User and Chat
    If there is no record, then create it
    If user is a member in two chats or more

    :param session: is connector to database from decorator @connection
    :param tg_id: (int) id of the user from telegram
    :param chat_id: (int) id of the chat from telegram
    :return: (int) count chat where user is member
    """

    is_private_chat = (tg_id == chat_id)  # Фильтр, чтобы в базу не добавлялся чат пользователя с ботом

    # Check if there is an entry in database:
    user_in_db = await get_one_user_link_with_chat(session, tg_id, chat_id)

    if not user_in_db and not is_private_chat:
        session.add(ChatUsers(tg_id=tg_id, chat_id=chat_id))
        await session.commit()


@connection
async def get_count_users_chat(session: async_session, tg_id: int) -> int:
    count_value = await session.scalar(select(func.count()).select_from(ChatUsers).where(ChatUsers.tg_id == tg_id))
    return count_value


@connection
async def set_user(session: async_session, tg_id, username: str = 'Null') -> None:
    """
    Function for writing a user to database

    :param session: is connector to database from decorator @connection
    :param tg_id: (int) id of the user from telegram
    :param username: (str) username of the user from telegram
    :return: None
    """

    user = await get_one_user_by_tgid(session, tg_id)

    if not user:
        session.add(User(tg_id=tg_id, tg_username=username))
        await session.commit()  # save info


@connection
async def set_chat(session: async_session, chat_id: int, chat_title) -> None:
    """
    Function for writing a chat's info to database

    :param session: is connector to database from decorator @connection
    :param chat_id: (int) id of the chat from telegram
    :param chat_title: (str) title of the chat from telegram
    :return: None
    """

    chat = await session.scalar(select(Chat).where(Chat.chat_id == chat_id))

    if not chat:
        session.add(Chat(chat_id=chat_id, chat_title=chat_title))
        await session.commit()  # save


@connection
async def get_list_of_users_chats(session: async_session, tg_id: int) -> list[str]:
    """
    Function for read database and get list of chats, where user is member

    :param session: is connector to database from decorator @connection
    :param tg_id: (int) id of the user from telegram
    :return: (str) list of chats as str
    """

    # Получаю список чатов, в которые вступил конкретный пользователь
    request_to_sql = select(Chat.chat_title).select_from(Chat)
    request_with_join = request_to_sql.join(ChatUsers, ChatUsers.chat_id == Chat.chat_id)
    request_with_filter = request_with_join.where(ChatUsers.tg_id == tg_id)
    data_from_db = await session.execute(request_with_filter)

    data_list = [chat_titile[0] for chat_titile in data_from_db]

    return data_list


@connection
async def get_list_chats(session: async_session) -> list:
    """
    Function for read database and get list of all chats

    :return: 'sqlalchemy.engine.row.Row' as [(<class Chat>,), (<class Chat>,)] list with classes of Chat
    """
    list_of_chats = await session.execute(select(Chat))
    return list_of_chats


@connection
async def check_karma(session: async_session, tg_id_sender: int, tg_id_recipient: int) -> tuple[User, User]:
    """
    The function is to connect to the database and receive the User's obj as tuple[User(Sender), User(Recipient)]

    :param session: is connector to database from decorator @connection
    :param tg_id_sender: (int) id of the user from telegram. Example: 123456
    :param tg_id_recipient: (int) id of the user from telegram. Example: 123456
    :return: tuple[User, User]
    """
    sender = await get_one_user_by_tgid(session, tg_id_sender)
    recipient = await get_one_user_by_tgid(session, tg_id_recipient)

    if not recipient:
        await set_user(tg_id_recipient)
        sender = await get_one_user_by_tgid(session, tg_id_sender)

    if not sender:
        await set_user(tg_id_sender)
        recipient = await get_one_user_by_tgid(session, tg_id_recipient)

    return sender, recipient


@connection
async def update_karma(session: async_session, tg_id_sender: int, tg_id_recipient: int) -> None:
    """
    The function is to connect to the database and update the value of sender's and recipient's karma

    :param session: is connector to database from decorator @connection
    :param tg_id_sender: (int) id of the user from telegram. Example: 123456
    :param tg_id_recipient: (int) id of the user from telegram. Example: 123456
    :return: None
    """
    s = await get_one_user_by_tgid(session, tg_id_sender)
    s.remove_karma_points()

    r = await get_one_user_by_tgid(session, tg_id_recipient)
    r.add_karma_value()

    session.add(s, r)
    await session.commit()


@connection
async def remove_link_from_db(session: async_session, tg_user_id: int, tg_chat_id) -> None:
    """
    The func removes the user's link with the chat from the database
    :param session: session of SQLAlchemy
    :param tg_user_id: (int) id of the user from telegram. Example: 123456
    :param tg_chat_id: (int) id of the chat from telegram. Example: -123456 or 123456
    :return: None
    """
    link_user_chat = await get_one_user_link_with_chat(session, tg_user_id, tg_chat_id)

    if link_user_chat:
        await session.delete(link_user_chat)
        logger.info(f'The link {link_user_chat.tg_id} <-> {link_user_chat.chat_id} has been deleted')

    await session.commit()
