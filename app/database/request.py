"""
Module with functions for requesting data from database
"""
# import libs
import aiohttp
import asyncio
import json

# import from libs
from datetime import datetime
from functools import wraps
from sqlalchemy import func, select
from typing import Coroutine

# import from modules
from app.database import (
    async_session,
    Base,
    ChatUsers,
    Chat,
    User,
    Project,
    ProjectSchema,
    TimestampsMixin,
    db_helper,
    crud_manager
)
from config import logger


def connection(function):
    """
    this decorator is used to make a database connection
    """

    @wraps(function)
    async def wrapper(*args, **kwargs):
        async for session in db_helper.session_getter():
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
    logger.info(f'The Chat {chat_title} {chat_id} has been saved')


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


async def check_karma(tg_id_sender: int, tg_id_recipient: int) -> tuple[User, User]:
    """
    The function is to connect to the database and receive the User's obj as tuple[User(Sender), User(Recipient)]

    :param tg_id_sender: (int) id of the user from telegram. Example: 123456
    :param tg_id_recipient: (int) id of the user from telegram. Example: 123456
    :return: tuple[User, User]
    """

    tasks = [crud_manager.user.get_user_by_tg_id(uid) for uid in [tg_id_sender, tg_id_recipient]]
    sender, recipient = await asyncio.gather(*tasks)

    if not recipient:
        recipient = await crud_manager.user.create_user(tg_id=tg_id_recipient)

    if not sender:
        sender = await crud_manager.user.create_user(tg_id=tg_id_sender)

    return sender, recipient


async def update_karma(tg_id_sender: int, tg_id_recipient: int) -> None:
    """
    The function is to connect to the database and update the value of sender's and recipient's karma

    :param tg_id_sender: (int) id of the user from telegram. Example: 123456
    :param tg_id_recipient: (int) id of the user from telegram. Example: 123456
    :return: None
    """
    tasks: list[Coroutine] = [crud_manager.user.get_user_by_tg_id(uid) for uid in [tg_id_sender, tg_id_recipient]]
    sender, recipient = await asyncio.gather(*tasks)  # type: User, User

    sender.remove_karma_points()
    recipient.add_karma_value()

    tasks: list[Coroutine] = [crud_manager.user.update(user) for user in [sender, recipient]]
    await asyncio.gather(*tasks)


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


async def create_project_of_user(project: Project) -> bool:
    new_project = ProjectSchema(
        prj_name=project.prj_name,
        prj_description=project.prj_description,
        prj_owner=project.prj_owner
    )
    project_as_dict = new_project.model_dump(by_alias=True)

    async with aiohttp.ClientSession() as session:
        async with session.post('https://api.mks-min.ru/projects', json=project_as_dict) as response:
            json_response = await response.json()
            status_code = response.status
    if status_code == 422:
        logger.error(f'ValidationError: {json_response}')
        return False
    if status_code == 400:
        logger.error(f'ValueError: {json_response}')
        return False

    logger.info(f'The new project {new_project.name} has been created by user {new_project.owner_id}')
    return True


async def get_list_of_projects(tg_user_id: int) -> dict[str, dict[str, any]]:
    async with aiohttp.ClientSession() as session:
        params = {"prj_owner": tg_user_id}
        async with session.get('https://api.mks-min.ru/projects', params=params) as response:
            if response.status == 200:
                return await response.json()


@connection
async def delete_entry(session: async_session, obj: Base):
    if not isinstance(obj, TimestampsMixin):
        raise TypeError(f'Object {obj} is not of type {TimestampsMixin}')

    class_object = type(obj)
    search_attr = class_object.get_search_attribute()
    search_value = getattr(obj, class_object.get_search_attribute_name())

    entry_looking_for = await session.scalar(select(class_object).where(search_attr == search_value))

    if entry_looking_for:
        entry_looking_for.deleted_at = datetime.utcnow()
        session.add(entry_looking_for)
        await session.commit()
