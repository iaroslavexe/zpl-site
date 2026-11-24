"""Сборка контекста страниц. Общая для FastAPI и статической сборки."""
from datetime import date

from app.config import (
    FANTASY_URL,
    SITE_URL,
    NAV,
    RULES_URL,
    SEASON,
    SEASON_TITLE,
    STATIC_DIR,
    TELEGRAM_URL,
    VK_PLAYLIST_URL,
    VK_URL,
)
from app.services import standings, stages as stages_service, stats as stats_service, streams

WEEKDAYS = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
MONTHS_FULL = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
    7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}


def days_word(days: int) -> str:
    if days % 10 == 1 and days % 100 != 11:
        return "день"
    if 2 <= days % 10 <= 4 and not 12 <= days % 100 <= 14:
        return "дня"
    return "дней"


def stage_view(stage: dict) -> dict:
    """Дополняет этап человекочитаемой датой и счётчиком дней."""
    try:
        value = date.fromisoformat(stage["date"])
    except (KeyError, ValueError):
        return {**stage, "human_date": "", "days_left": None, "days_word": ""}

    left = (value - date.today()).days
    end_raw = stage.get("end_date")
    if end_raw:
        end = date.fromisoformat(end_raw)
        if end.month == value.month:
            human = f"{value.day}–{end.day} {MONTHS_FULL[value.month]}"
        else:
            human = f"{value.day} {MONTHS_FULL[value.month]} – {end.day} {MONTHS_FULL[end.month]}"
    else:
        human = f"{value.day} {MONTHS_FULL[value.month]}, {WEEKDAYS[value.weekday()]}"

    return {
        **stage,
        "day_month": f"{value.day} {MONTHS_FULL[value.month]}",
        "weekday": WEEKDAYS[value.weekday()],
        "human_date": human,
        "days_left": left if left > 0 else None,
        "days_word": days_word(left),
    }


def pdf_size(path_part: str) -> str:
    """Размер файла для подписи: «12,9 МБ»."""
    file = STATIC_DIR / path_part.replace("/static/", "", 1)
    if not file.exists():
        return ""
    return f"{file.stat().st_size / 1048576:.1f} МБ".replace(".", ",")


def _base(active: str, canonical: str = "", **extra) -> dict:
    return {
        "nav": NAV,
        "site_url": SITE_URL,
        "canonical": canonical,
        "active": active,
        "season": SEASON,
        "season_title": SEASON_TITLE,
        "telegram_url": TELEGRAM_URL,
        "vk_url": VK_URL,
        "vk_games_url": VK_PLAYLIST_URL,
        "fantasy_url": FANTASY_URL,
        **extra,
    }


def league() -> tuple[str, dict]:
    table = standings.build()
    stages = [stage_view(item) for item in table["stages"]]
    upcoming = next((item for item in stages if item.get("status") == "upcoming"), None)
    streams_data = streams.build()
    video = (streams_data.get("clips") or [None])[-1]
    return "pages/league.html", _base(
        "league",
        canonical="/",
        top=table["rows"][:4],
        next_stage=upcoming,
        tops=stats_service.tops(4),
        video=video,
        video_stage=streams_data.get("stage_title", ""),
    )


def standings_page() -> tuple[str, dict]:
    return "pages/standings.html", _base("standings", canonical="/standings", table=standings.build())


def stages(stage: str = "") -> tuple[str, dict]:
    items = stages_service.stage_list()
    played = [item for item in items if item.get("games")]
    default_id = played[-1]["id"] if played else (items[0]["id"] if items else "")
    current_id = stage or default_id

    tabs, panels = [], []
    for item in items:
        page = stages_service.build(item["id"])
        tabs.append({"id": item["id"], "title": item["title"]})
        panels.append({
            "id": item["id"],
            "active": item["id"] == current_id,
            "human": stage_view(page["stage"]) if page["stage"] else None,
            "blocks": page["blocks"],
            "teams": page["teams"],
            "games_count": page["games_count"],
        })

    return "pages/stages.html", _base(
        "stages", canonical="/stages", tabs=tabs, panels=panels, current_id=current_id
    )


def stats() -> tuple[str, dict]:
    return "pages/stats.html", _base("stats", canonical="/stats", stats=stats_service.build())


def rules() -> tuple[str, dict]:
    return "pages/rules.html", _base(
        "rules",
        canonical="/rules",
        rules_url=RULES_URL,
        rules_pages=22,
        rules_size=pdf_size(RULES_URL),
    )


def not_found() -> tuple[str, dict]:
    return "pages/404.html", _base("")
