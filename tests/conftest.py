import json

from collections.abc import AsyncGenerator

import pytest

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from src.api.dependencies import get_db
from src.config import settings
from src.connectors.database_init import (
    BaseORM,
    async_session_maker_null_pool,
    engine_null_pool,
)
from src.main import app
from src.managers.db_manager import DBManager
from src.models import *  # noqa: F403
from src.schemas.feature import FeatureRequest


class DataDB:
    point_data: None
    line_data: None
    polygon_data: None
    example_collection_data: None


data = DataDB()

with open(file="example_point.json", encoding="utf-8") as e_p:
    data.point_data = json.load(e_p)

with open(file="example_line_string.json", encoding="utf-8") as e_l_s:
    data.line_data = json.load(e_l_s)

with open(file="example_polygon.json", encoding="utf-8") as e_pl:
    data.polygon_data = json.load(e_pl)

with open(file="example_collection.json", encoding="utf-8") as e_c:
    data.example_collection_data = json.load(e_c)


@pytest.fixture(scope="session", autouse=True)
def check_test_mode() -> None:
    assert settings.MODE == "TEST"


@pytest.fixture(scope="session", autouse=True)
async def async_setup_db(check_test_mode) -> None:
    async with engine_null_pool.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: sync_conn.execute(
                text("CREATE EXTENSION IF NOT EXISTS postgis")
            )
        )
        await conn.run_sync(BaseORM.metadata.drop_all)
        await conn.run_sync(BaseORM.metadata.create_all)


async def get_db_null_pool() -> AsyncGenerator[DBManager, None]:
    async with DBManager(
        session_factories=async_session_maker_null_pool
    ) as db:
        yield db


@pytest.fixture(scope="session")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test.ru"
    ) as ac:
        yield ac


app.dependency_overrides[get_db] = get_db_null_pool


@pytest.fixture(scope="session", autouse=True)
async def async_fill_db(async_setup_db) -> None:
    point = FeatureRequest.model_validate(data.point_data)
    line = FeatureRequest.model_validate(data.line_data)
    polygon = FeatureRequest.model_validate(data.polygon_data)
    async with DBManager(
        session_factories=async_session_maker_null_pool
    ) as db_:
        await db_.feature.add(point)
        await db_.feature.add(line)
        await db_.feature.add(polygon)
        await db_.commit()
