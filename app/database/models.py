# Здесь подключаюсь к БД и создаю нужные таблицы

# Импорт библиотек
import asyncio

# Импорт функций из библиотек
from sqlalchemy import Column, BigInteger, String, Integer, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

# Импорт из файлов
from config.config import get_tokens

# Создаем подключение к БД
post_host_token = asyncio.run(get_tokens('PostSQL_host'))
engine = create_async_engine(url=post_host_token,
                             echo=False)  # Создаем БД
async_session = async_sessionmaker(engine)  # Подключаемся к БД


class Base(AsyncAttrs, DeclarativeBase):  # Основной класс, который дочерний к sqlalchemy
    pass


class User(Base):  # Таблица, которая хранит юзеров
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id = mapped_column(BigInteger, nullable=False, unique=True)
    tg_username: Mapped[str] = mapped_column(String(30), nullable=True)
    karma_start_value: Mapped[int] = mapped_column(nullable=False, default=5)
    total_karma: Mapped[int] = mapped_column(nullable=False, default=0)


class Chat(Base):  # таблица с чатами, в которых бот админ
    __tablename__ = 'chats'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id = mapped_column(BigInteger, nullable=False, unique=True)
    chat_title: Mapped[str] = mapped_column(String(120), nullable=True, default='null')


class ChatUsers(Base):  # Таблица, которая связывает конкретного пользователя, с конкретным чатом
    __tablename__ = 'chatAndUsers'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id = mapped_column(BigInteger, ForeignKey('users.tg_id'), nullable=False)
    chat_id = mapped_column(BigInteger, ForeignKey('chats.chat_id'), nullable=False)


async def async_main():  # Функция создает все таблицы, если их не существует
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all():  # Удаляет все таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
