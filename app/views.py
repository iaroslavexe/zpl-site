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


def _plural(number: int, one: str, few: str, many: str) -> str:
    if number % 10 == 1 and number % 100 != 11:
        return one
    if 2 <= number % 10 <= 4 and not 12 <= number % 100 <= 14:
        return few
    return many


def archive_landing() -> tuple[str, dict]:
    from app.services import archive

    d = archive.data()
    summary = archive.summary()
    summary["seasons_word"] = _plural(summary["seasons"], "сезон", "сезона", "сезонов")
    summary["stages_word"] = _plural(summary["stages"], "этап", "этапа", "этапов")
    summary["teams_word"] = _plural(summary["teams"], "команда", "команды", "команд")
    summary["players_word"] = _plural(summary["players"], "игрок", "игрока", "игроков")

    top_games = max(d["players"], key=lambda p: p.get("games") or 0)
    top_goals = max(d["players"], key=lambda p: p["goals"])
    top_assists = max(d["players"], key=lambda p: p["assists"])

    teams_by_id = d["team_by_id"]
    champs = []
    for row in archive.champions():
        winner = row["teams"][0] if row["teams"] else None
        team = next((t for t in d["teams"] if winner and t["name"] == winner[0]), None)
        champs.append({
            "season": row["season"],
            "winner": winner[0] if winner else "—",
            "avatar": team["avatar"] if team else None,
            "runners": [t[0] for t in row["teams"][1:]],
            "team_id": team["id"] if team else None,
        })

    return "pages/archive.html", _base(
        "archive",
        canonical="/archive",
        summary=summary,
        champions=champs,
        leaders=[
            {"player": top_games, "value": top_games["games"], "unit": "игр"},
            {"player": top_goals, "value": top_goals["goals"], "unit": "голов"},
            {"player": top_assists, "value": top_assists["assists"], "unit": "ассистов"},
        ],
    )


def archive_catalog(tab: str = "seasons") -> tuple[str, dict]:
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
            winners[stage["id"]] = first[0]

    teams_view = sorted(
        d["teams"],
        key=lambda t: (-len(t["stages"]), -(t["gold"] + t["silver"]), t["name"]),
    )

    title_counts = {}
    for row in archive.champions():
        if not row["teams"]:
            continue
        name = row["teams"][0][0]
        team = next((t for t in d["teams"] if t["name"] == name), None)
        if team:
            title_counts[team["id"]] = title_counts.get(team["id"], 0) + 1

    players_view = []
    for player in d["players"]:
        names = []
        for season in player["seasons"]:
            for tid in season["teams"]:
                name = d["team_by_id"].get(tid, {}).get("name", tid)
                if name not in names:
                    names.append(name)
        players_view.append({**player, "team_names": names})

    records = []
    d_games = [g for g in d["games"] if g["hs"] is not None and g["vs"] is not None]
    if d_games:
        big = max(d_games, key=lambda g: abs((g["hs"] or 0) - (g["vs"] or 0)))
        records.append(("Крупнейшая победа",
                        f'{big["home_name"]} — {big["away_name"]} {big["hs"]}:{big["vs"]}',
                        f'/archive/game/{big["id"]}'))
        high = max(d_games, key=lambda g: (g["hs"] or 0) + (g["vs"] or 0))
        records.append(("Самая результативная игра",
                        f'{high["home_name"]} — {high["away_name"]} {high["hs"]}:{high["vs"]}',
                        f'/archive/game/{high["id"]}'))
    if d["players"]:
        top = max(d["players"], key=lambda p: p["goals"])
        records.append(("Больше всех голов", f'{top["name"]} — {top["goals"]}', f'/archive/player/{top["id"]}'))
    if d["teams"]:
        best = max(d["teams"], key=lambda t: (t["gold"], t["silver"]))
        records.append(("Больше всех золота", f'{best["name"]} — {best["gold"]}', f'/archive/team/{best["id"]}'))

    def stage_name(stage: dict) -> str:
        title = stage["title"].lower()
        if "финал" in title:
            return "Финал"
        label = stage["title"].split(".")[-1].split("этап")[0].strip()
        label = (label.replace("l", "I").replace("L", "I")
                 .replace("1V", "IV").replace("Il", "II").replace("Ill", "III").upper())
        return f"{label} этап" if label else "Этап"

    stages_view = []
    for stage in sorted(d["stages"], key=lambda s: s["date"], reverse=True):
        stage["name"] = stage_name(stage)
        stages_view.append(stage)

    grouped = []
    for season in reversed(archive.SEASONS):
        items = [s for s in stages_view if s["season"] == season]
        if items:
            grouped.append({"season": season, "stages": items})

    return "pages/archive_catalog.html", _base(
        "archive",
        canonical=f"/archive/{tab}",
        teams_by_id=d["team_by_id"],
        title_counts=title_counts,
        records=records,
        winners=winners,
        tab=tab,
        summary=archive.summary(),
        champions=archive.champions(),
        seasons=seasons,
        matrix_central=_archive_matrix("Центральный"),
        matrix_spb=_archive_matrix("Северо-Западный"),
        stages=stages_view,
        stage_groups=grouped,
        teams=teams_view,
        players=players_view,
    )


def archive_entity() -> tuple[str, dict]:
    return "pages/archive_entity.html", _base("archive", canonical="/archive")


