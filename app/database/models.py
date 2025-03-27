"""
Create tables in DataBase
"""

# import libraries
import asyncio
import uuid

# import from libraries
from datetime import datetime
from pydantic import BaseModel, Field, UUID4, ConfigDict
from sqlalchemy import BigInteger, ForeignKey, String, Integer, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
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


class SearchableMixin:
    @classmethod
    def get_search_attribute(cls):
        """Возвращает атрибут, по которому выполняется поиск (по умолчанию `id`)."""
        return cls.id  # или другой атрибут по умолчанию

    @classmethod
    def get_search_attribute_name(cls):
        """Возвращает имя атрибута для поиска (опционально)."""
        return "id"


class User(SearchableMixin, TimestampsMixin, Base):
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

    @classmethod
    def get_search_attribute(cls):
        return cls.tg_id

    @classmethod
    def get_search_attribute_name(cls):
        return "tg_id"


class Chat(Base):
    """
    Table with data of chats
    """
    __tablename__ = 'chats'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id = mapped_column(BigInteger, nullable=False, unique=True)
    chat_title: Mapped[str] = mapped_column(String(120), nullable=True, default='null')
    project_id = mapped_column(UUID(as_uuid=True), ForeignKey('projects.uuid'), nullable=True, unique=False)

    prj = relationship('Project', back_populates='chat', uselist=False)


class ChatUsers(SearchableMixin, TimestampsMixin, Base):
    """
    A table linking the chats and the users who joined them
    """
    __tablename__ = 'chatandusers'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id = mapped_column(BigInteger, ForeignKey('users.tg_id'), nullable=False)
    chat_id = mapped_column(BigInteger, ForeignKey('chats.chat_id'), nullable=False)

    @classmethod
    def get_search_attribute(cls):
        return cls.tg_id

    @classmethod
    def get_search_attribute_name(cls):
        return "tg_id"


class Project(SearchableMixin, TimestampsMixin, Base):
    __tablename__ = 'projects'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        unique=True
    )
    prj_name: Mapped[str] = mapped_column(String(50), nullable=True)
    prj_description: Mapped[str] = mapped_column(String(200), nullable=True)
    prj_owner = mapped_column(BigInteger, ForeignKey('users.tg_id'), nullable=False)

    chat = relationship('Chat', back_populates='prj')

    @classmethod
    def get_search_attribute(cls):
        return cls.prj_name

    @classmethod
    def get_search_attribute_name(cls):
        return "prj_name"

    def __str__(self):
        return (f'<Project('
                f'id={self.id},'
                f'uuid={self.uuid},'
                f'prj_name={self.prj_name},'
                f'prj_description={self.prj_description},'
                f'prj_owner={self.prj_owner})>')


class ProjectSchema(BaseModel):
    """
    Схема для ответа от сервера (сервер -> клиент)
    """

    name: str | None = Field(
        None,
        min_length=3,
        max_length=50,
        alias="prj_name",
    )
    description: str | None = Field(
        None,
        max_length=200,
        alias="prj_description",
    )
    owner_id: int = Field(
        ..., alias="prj_owner", json_schema_extra={"example": 123456789}
    )
    model_config = ConfigDict(
        extra="ignore",
        json_schema_extra={
            "example": {
                "prj_name": "Test project",
                "prj_description": "Test project description",
                "prj_owner": 123456,
            }
        },
    )
