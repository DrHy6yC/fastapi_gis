from fastapi import APIRouter, Body, Path, status, HTTPException
from src.api.dependencies import DBDep
from src.exeptions.error import ObjectNotFoundError
from src.openapi_examples import LineString, Point, Polygon
from src.schemas.feature import FeatureCollection, FeatureRequest
from src.schemas.message import Message, MessageID

router = APIRouter(prefix="/features", tags=["Управление геометрией"])


@router.post(
    path="",
    summary="Добавление объекта",
    status_code=status.HTTP_201_CREATED,
)
async def create_feature(
    db: DBDep,
    data: FeatureRequest = Body(
        openapi_examples={"1": Point, "2": LineString, "3": Polygon},
    ),
) -> MessageID:
    feature_id = await db.feature.add(data)
    await db.commit()
    return MessageID(id=feature_id)


@router.get(path="", summary="Получение всех объектов")
async def get_feature_collection(
    db: DBDep,
) -> FeatureCollection:
    return await db.feature.get_feature_collection()


@router.delete(path="/{feature_id}", summary="Удаление объекта", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature(
    db: DBDep, feature_id: int = Path(description="Айди объекта")
) -> None:
    try:
        await db.feature.delete(id=feature_id)
    except ObjectNotFoundError as ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ex.detail)
    await db.commit()
