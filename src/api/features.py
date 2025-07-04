from fastapi import APIRouter, Body, Path

from src.api.dependencies import DBDep
from src.openapi_examples import Polygon, Point, LineString
from src.schemas.feature import FeatureRequest
from src.schemas.message import Message


router = APIRouter(prefix="/features", tags=["Управление геометрией"])


@router.post(
    path="/",
    summary="Добавление объекта",
)
async def create_feature(
    db: DBDep,
    data: FeatureRequest = Body(
        openapi_examples={
            "1": Point,
            "2": LineString,
            "3": Polygon
        },
    ),
) -> int:
    feature_id = await db.feature.add(data)
    await db.commit()
    return feature_id


@router.get(path="/", summary="Получение всех объектов")
async def get_all_features():
    pass


@router.delete(path="/{feature_id}", summary="Удаление объекта")
async def delete_feature(
        db: DBDep,
        feature_id: int = Path(description="Айди объекта")
) -> Message:
    await db.feature.delete(id=feature_id)
    await db.commit()
    return Message(detail="OK")
