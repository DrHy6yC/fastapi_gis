from typing import Annotated

from fastapi import Depends

from src.connectors.database_init import async_session_maker
from src.managers.db_manager import DBManager


async def get_db():
    async with DBManager(session_factories=async_session_maker) as db:
        yield db


DBDep = Annotated[DBManager, Depends(get_db)]
