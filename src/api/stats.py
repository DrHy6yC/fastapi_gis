from fastapi import APIRouter
from src.api.dependencies import DBDep

router = APIRouter(prefix="/stats", tags=["Статистика"])


@router.get(path="", summary="Получить статистику по типам")
async def get_stats(db: DBDep) -> dict[str, int]:
    return await db.feature.get_feature_count_by_type()
