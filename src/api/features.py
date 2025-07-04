from fastapi import APIRouter, Body

from src.api.dependencies import DBDep
from src.openapi_examples import Polygon, Point
from src.schemas.feature import FeatureRequest
from src.schemas.message import Message


router = APIRouter(prefix="/features", tags=["Управление геометрией"])


@router.post(path="/", summary="Добавление объекта",)
async def create_feature(
        db: DBDep,
        data: FeatureRequest = Body(
        openapi_examples={
            "1": Point,
            "2": Polygon,
        },
    )
) -> int:
    feature_id = await db.feature.add(data)
    await db.commit()
    return feature_id


@router.get(path="/", summary="Получение всех объектов")
async def get_all_features():
    pass


@router.delete(path="/", summary="Удаление объекта")
async def delete_feature(db: DBDep) -> Message:
    await db.feature.delete()
    await db.commit()
    return Message(detail="OK")
