from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.api.dependencies import DBDep

router = APIRouter(prefix="", tags=["Статистика"])
templates = Jinja2Templates(directory="src/templates")


@router.get("/", response_class=HTMLResponse, summary="Главная/Дашбоард")
async def read_root(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get(path="/stats", summary="Получить статистику по типам")
async def get_stats(db: DBDep) -> dict[str, int]:
    return await db.feature.get_feature_count_by_type()
