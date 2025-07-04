from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from src.config import settings

engine = create_async_engine(
    url=settings.db_url,
    echo=True,
)


async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


class BaseORM(DeclarativeBase):
    pass
