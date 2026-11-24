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


# ---------- Архив ----------

def _archive_matrix(division: str) -> dict:
    from app.services import archive

    d = archive.data()
    stages = [s for s in d["stages"]
              if s["division"] == division or "финал" in s["title"].lower()]
    stages.sort(key=lambda s: s["date"])

    played, wins, home_div = {}, {}, {}
    for stage in d["stages"]:
        for tid, place, _div in stage["places"]:
            played[tid] = played.get(tid, 0) + 1
            wins[tid] = wins.get(tid, 0) + (1 if place == 1 else 0)
            if "финал" not in stage["title"].lower():
                home_div.setdefault(tid, stage["division"])

    team_ids = [t for t in played if home_div.get(t) == division]
    team_ids.sort(key=lambda t: (-wins.get(t, 0), -played.get(t, 0), d["team_by_id"][t]["name"]))

    cells = {}
    for stage in stages:
        for tid, place, div in stage["places"]:
            cells[(tid, stage["id"])] = (place, div)

    for stage in stages:
        label = stage["title"].split(".")[-1].strip()
        label = label.split("этап")[0].strip() or label
        stage["label"] = (label.replace("l", "I").replace("L", "I")
                          .replace("1V", "IV").replace("Il", "II").replace("Ill", "III"))
    return {"stages": stages, "teams": team_ids, "cells": cells}


def archive_landing(tab: str = "seasons") -> tuple[str, dict]:
    from app.services import archive

    d = archive.data()
    seasons = []
    for season in archive.SEASONS:
        items = [s for s in d["stages"] if s["season"] == season]
        seasons.append({
            "season": season,
            "stages": items,
            "teams": len({t for s in items for t, _, _ in s["places"]}),
            "games": sum(s["games_count"] for s in items),
        })

    winners = {}
    for stage in d["stages"]:
        first = [t for t, place, _ in stage["places"] if place == 1]
        if first:
            winners[stage["id"]] = d["team_by_id"].get(first[0], {}).get("name", first[0])

    players_view = []
    for player in d["players"]:
        names = []
        for season in player["seasons"]:
            for tid in season["teams"]:
                name = d["team_by_id"].get(tid, {}).get("name", tid)
                if name not in names:
                    names.append(name)
        players_view.append({**player, "team_names": names})

    return "pages/archive.html", _base(
        "archive",
        canonical="/archive",
        teams_by_id=d["team_by_id"],
        winners=winners,
        tab=tab,
        summary=archive.summary(),
        champions=archive.champions(),
        seasons=seasons,
        matrix_central=_archive_matrix("Центральный"),
        matrix_spb=_archive_matrix("Северо-Западный"),
        stages=sorted(d["stages"], key=lambda s: s["date"], reverse=True),
        teams=d["teams"],
        players=players_view,
    )


def archive_stage(slug: str) -> tuple[str, dict] | None:
    from app.services import archive

    stage = archive.stage(slug)
    if not stage:
        return None
    d = archive.data()
    seats = [(d["team_by_id"].get(t, {}).get("name", t), p, div) for t, p, div in stage["places"]]
    seats.sort(key=lambda r: r[1])
    sotg = sorted([(d["team_by_id"].get(t, {}).get("name", t), spirit, games)
                   for t, spirit, games in stage["sotg"]], key=lambda r: -r[1])
    return "pages/archive_stage.html", _base(
        "archive", canonical=f"/archive/stage/{slug}", stage=stage, seats=seats, sotg=sotg
    )


def archive_team(team_id: str) -> tuple[str, dict] | None:
    from app.services import archive

    team = archive.team(team_id)
    if not team:
        return None
    d = archive.data()
    stages = []
    for sid, place, div in team["stages"]:
        stage = d["stage_by_id"][sid]
        stages.append({"stage": stage, "place": place, "division": div})
    stages.sort(key=lambda item: item["stage"]["date"])

    players = [p for p in d["players"] if any(team_id in s["teams"] for s in p["seasons"])]
    players.sort(key=lambda p: (-(p["goals"] + p["assists"]), -p["stages"]))

    return "pages/archive_team.html", _base(
        "archive", canonical=f"/archive/team/{team_id}", team=team, stages=stages, players=players
    )


def archive_player(player_id: str) -> tuple[str, dict] | None:
    from app.services import archive

    player = archive.player(player_id)
    if not player:
        return None
    d = archive.data()
    seasons = []
    for season in player["seasons"]:
        teams = [d["team_by_id"].get(t, {}).get("name", t) for t in season["teams"]]
        seasons.append({**season, "team_names": teams})
    return "pages/archive_player.html", _base(
        "archive", canonical=f"/archive/player/{player_id}", player=player, seasons=seasons
    )


def archive_game(game_id: int) -> tuple[str, dict] | None:
    from app.services import archive

    game = archive.game(game_id)
    if not game:
        return None
    d = archive.data()
    names = {}
    for row in game["timeline"]:
        for pid in (row[2], row[3]):
            if pid and pid not in names:
                names[pid] = d["player_by_id"].get(pid, {}).get("name", pid)
    return "pages/archive_game.html", _base(
        "archive", canonical=f"/archive/game/{game_id}", game=game,
        stage=d["stage_by_id"].get(game["stage"]), names=names,
    )
