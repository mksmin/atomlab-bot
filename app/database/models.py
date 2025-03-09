"""
Create tables in DataBase
"""

# import libraries
import asyncio
import uuid

# import from libraries
from datetime import datetime
from sqlalchemy import BigInteger, ForeignKey, String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.dialects.postgresql import UUID

# import from modules
from config import get_tokens, dbconf

# create engine and connection to DB
post_host_token = asyncio.run(get_tokens('PostSQL_host'))
engine = create_async_engine(url=post_host_token,
                             echo=dbconf.echo_mode)  # create engine
async_session = async_sessionmaker(engine)  # create session func


class Base(AsyncAttrs, DeclarativeBase):
    """
    Main class
    """
    pass


class TimestampsMixin:
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=True)
    deleted_at: Mapped[datetime] = mapped_column(default=None, server_default=None, nullable=True)


class User(TimestampsMixin, Base):
    """
    Table with data of users
    """

    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id = mapped_column(BigInteger, nullable=False, unique=True)
    tg_username: Mapped[str] = mapped_column(String(30), nullable=True)
    karma_start_value: Mapped[int] = mapped_column(nullable=False, default=20, server_default='20')
    total_karma: Mapped[int] = mapped_column(nullable=False, default=0, server_default='0')
    user_status: Mapped[str] = mapped_column(String(30), nullable=True, server_default='user', default='user')

    def remove_karma_points(self):
        self.karma_start_value -= 1

    def add_karma_value(self):
        self.total_karma += 1


class Chat(Base):
    """
    Table with data of chats
    """
    __tablename__ = 'chats'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id = mapped_column(BigInteger, nullable=False, unique=True)
    chat_title: Mapped[str] = mapped_column(String(120), nullable=True, default='null')


class ChatUsers(TimestampsMixin, Base):
    """
    A table linking the chats and the users who joined them
    """
    __tablename__ = 'chatandusers'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id = mapped_column(BigInteger, ForeignKey('users.tg_id'), nullable=False)
    chat_id = mapped_column(BigInteger, ForeignKey('chats.chat_id'), nullable=False)


class Project(TimestampsMixin, Base):
    __tablename__ = 'projects'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid = mapped_column(UUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    prj_name: Mapped[str] = mapped_column(String(50), nullable=True)
    prj_description: Mapped[str] = mapped_column(String(200), nullable=True)
    prj_owner = mapped_column(BigInteger, ForeignKey('users.tg_id'), nullable=False)
