"""
Create tables in DataBase
"""

# import libraries
import asyncio

# import from libraries
from sqlalchemy import Column, BigInteger, String, Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

# import from modules
from config.config import get_tokens

# create engine and connection to DB
post_host_token = asyncio.run(get_tokens('PostSQL_host'))
engine = create_async_engine(url=post_host_token,
                             echo=False)  # create engine
async_session = async_sessionmaker(engine)  # create session func


class Base(AsyncAttrs, DeclarativeBase):  # main class
    pass


class User(Base):  # table with data of users
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id = mapped_column(BigInteger, nullable=False, unique=True)
    tg_username: Mapped[str] = mapped_column(String(30), nullable=True)
    karma_start_value: Mapped[int] = mapped_column(nullable=False, default=5)
    total_karma: Mapped[int] = mapped_column(nullable=False, default=0)


class Chat(Base):  # table with data of chats
    __tablename__ = 'chats'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id = mapped_column(BigInteger, nullable=False, unique=True)
    chat_title: Mapped[str] = mapped_column(String(120), nullable=True, default='null')


class ChatUsers(Base):  # Таблица, которая связывает конкретного пользователя, с конкретным чатом
    __tablename__ = 'chatAndUsers'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id = mapped_column(BigInteger, ForeignKey('users.tg_id'), nullable=False)
    chat_id = mapped_column(BigInteger, ForeignKey('chats.chat_id'), nullable=False)


async def async_main() -> None:
    """
    func create all tables in database
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all() -> None:
    """
    func drop all tables in database
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
