from fastapi import APIRouter

router = APIRouter(prefix="/features", tags=["Управление геометрией"])


@router.post(path="/", summary="Добавление объекта")
async def create_feature():
    pass


@router.get(path="/", summary="Получение всех объектов")
async def get_all_features():
    pass


@router.delete(path="/", summary="Удаление объекта")
async def delete_feature():
    pass
