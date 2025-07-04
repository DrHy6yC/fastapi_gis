from fastapi import APIRouter
from src.api.dependencies import DBDep

router = APIRouter(prefix="/stats", tags=["Статистика"])


@router.get(path="", summary="Получить статистику по типам")
async def get_stats(db: DBDep) -> dict:
    return await db.feature.get_feature_count_by_type()
