from fastapi import APIRouter

router = APIRouter(prefix="/stats", tags=["Статистика"])


@router.get(path="/", summary="Получить статистику по типам")
async def get_stats():
    pass
