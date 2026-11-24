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


@router.get("/archive", response_class=HTMLResponse)
def archive_page(request: Request, tab: str = "seasons"):
    return _render(request, views.archive_landing(tab))


@router.get("/archive/stage/{slug}", response_class=HTMLResponse)
def archive_stage_page(request: Request, slug: str):
    page = views.archive_stage(slug)
    if not page:
        return _render(request, views.not_found())
    return _render(request, page)


@router.get("/archive/team/{team_id}", response_class=HTMLResponse)
def archive_team_page(request: Request, team_id: str):
    page = views.archive_team(team_id)
    if not page:
        return _render(request, views.not_found())
    return _render(request, page)


@router.get("/archive/player/{player_id}", response_class=HTMLResponse)
def archive_player_page(request: Request, player_id: str):
    page = views.archive_player(player_id)
    if not page:
        return _render(request, views.not_found())
    return _render(request, page)


@router.get("/archive/game/{game_id}", response_class=HTMLResponse)
def archive_game_page(request: Request, game_id: int):
    page = views.archive_game(game_id)
    if not page:
        return _render(request, views.not_found())
    return _render(request, page)
