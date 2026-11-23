"""Роуты сайта: тонкий слой над app.views."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app import views
from app.config import TEMPLATES_DIR

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)


def _render(request: Request, page: tuple[str, dict]) -> HTMLResponse:
    name, context = page
    return templates.TemplateResponse(name, {"request": request, **context})


@router.get("/", response_class=HTMLResponse)
def league_page(request: Request):
    return _render(request, views.league())


@router.get("/standings", response_class=HTMLResponse)
def standings_page(request: Request):
    return _render(request, views.standings_page())


@router.get("/stages", response_class=HTMLResponse)
def stages_page(request: Request, stage: str = ""):
    return _render(request, views.stages(stage))


@router.get("/stats", response_class=HTMLResponse)
def stats_page(request: Request):
    return _render(request, views.stats())


@router.get("/rules", response_class=HTMLResponse)
def rules_page(request: Request):
    return _render(request, views.rules())
