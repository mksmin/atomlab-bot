# import libs
import asyncio

# import from libs
from contextlib import asynccontextmanager
from functools import wraps
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import TypeVar, Generic, Type, AsyncGenerator, ParamSpec, Callable, Concatenate, Any, Coroutine

# import from modules
from app.database.models import User
from app.database.db_helper import db_helper
from config import logger

# global
ModelType = TypeVar("ModelType")
P = ParamSpec("P")
R = TypeVar("R")


class BaseCRUDManager(Generic[ModelType]):
    def __init__(
            self,
            session_factory: async_sessionmaker[AsyncSession],
            model: Type[ModelType]
    ):
        self.session_factory = session_factory
        self.model = model

    @asynccontextmanager
    async def _get_session(self):
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Ошибка при работе с базой данных")
            raise
        finally:
            await session.close()

    @staticmethod
    def auto_session(func: Callable[Concatenate["BaseCRUDManager[ModelType]", P], Coroutine[Any, Any, R]]) -> Callable[
        Concatenate["BaseCRUDManager[ModelType]", P], Coroutine[Any, Any, R]
    ]:
        @wraps(func)
        async def wrapper(self: "BaseCRUDManager[ModelType]", *args: P.args, **kwargs: P.kwargs) -> R:
            async with self._get_session() as session:
                kwargs["session"] = session
                return await func(self, *args, **kwargs)

        return wrapper

    @auto_session
    async def _exist_by_field(self, field: str, value: str | int, *, session: AsyncSession) -> bool:
        """
        Check if the record exists in the database
        :param field: any field name, which exists in the model
        :param value: any value with the same type as in the field
        :return: True if the record exists, otherwise False
        """

        query = select(self.model).where(getattr(self.model, field) == value)
        result = await session.execute(query)
        return result.scalar_one_or_none() is not None

    @auto_session
    async def create(self, session: AsyncSession, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        session.add(instance)
        await session.flush()
        await session.refresh(instance)
        logger.info(f"Created entry of {self.model.__name__} model with id={instance.id}")
        return instance

    @auto_session
    async def get_one(self, session: AsyncSession, search_value: str | int, search_field: str = "default") -> ModelType:
        if hasattr(self.model, 'get_search_attribute') and callable(
                self.model.get_search_attribute) and search_field == "default":
            attribute = self.model.get_search_attribute()
        else:
            attribute = getattr(self.model, search_field, None)

        if attribute is None:
            raise ValueError(f"Field '{search_field}' does not exist in the model '{self.model.__name__}'")

        query = select(self.model).where(attribute == search_value)
        result = await session.execute(query)
        instance = result.scalar_one_or_none()
        return instance

    @auto_session
    async def update(self, instance: ModelType, *, session: AsyncSession, **kwargs):
        if not await self._exist_by_field("id", instance.id):
            raise ValueError(f"Entry with id={instance.id} not found in {self.model.__name__} model")

        session.add(instance)
        logger.info(f"Updated entry of {self.model.__name__} model with id={instance.id}")


class UserManager(BaseCRUDManager):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(session_factory, model=User)

    auto_session = BaseCRUDManager.auto_session

    async def get_user_by_tg_id(self, user_tg_id: int) -> User | None:
        logger.info(f"Getting user with tg_id={user_tg_id}...")
        return await super().get_one(search_value=user_tg_id)

    async def create_user(self, tg_id: int, *, username: str = None) -> User:
        if await self._exist_by_field("tg_id", tg_id):
            user = await self.get_user_by_tg_id(tg_id)
            if user.tg_username != username:
                user.tg_username = username
                await super().update(instance=user)
                logger.info(f"Updated {User.__name__} with id={user.id}")
        else:
            user = await super().create(tg_id=tg_id, tg_username=username)
            logger.info(f"Created {User.__name__} with id={user.id}")
        return user


class CRUDManager:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.user: UserManager = UserManager(session_factory)


crud_manager = CRUDManager(db_helper.session_factory)
