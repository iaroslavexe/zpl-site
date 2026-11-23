"""Статистика игроков: снимок из фэнтези + подготовка к выводу."""
from app.services.storage import load
from app.services.teams import normalize

def build() -> dict:
    data = load("player_stats.json")
    players = data.get("players", [])
    stages = data.get("stages", [])

    # этапы, за которые есть хоть одна запись — только их показываем в табах
    used = {key for player in players for key in (player.get("by_stage") or {})}
    with_data = [stage for stage in stages if str(stage["id"]) in used]

    rosters = load("rosters.json")

    for player in players:
        player["team"] = normalize(player.get("team"))
        by_stage = player.get("by_stage") or {}
        teams = {}
        for stage_id in by_stage:
            team = (rosters.get(str(stage_id)) or {}).get(player.get("name"))
            if team:
                teams[str(stage_id)] = team
        player["teams_by_stage"] = teams
        player["teams"] = list(dict.fromkeys(teams[k] for k in sorted(teams)))

    rows = sorted(players, key=lambda p: (-p.get("goals", 0), -p.get("assists", 0), p.get("name", "")))

    return {
        "players": rows,
        "stages": stages,
        "with_data": with_data,
        "aliases": load("team_aliases.json"),
        "total": len(rows),
    }


def tops(limit: int = 4) -> dict:
    """Топ игроков по голам, ассистам и блокам за все этапы."""
    players = load("player_stats.json").get("players", [])

    def best(key: str) -> list[dict]:
        return sorted(players, key=lambda p: (-p.get(key, 0), p.get("name", "")))[:limit]

    return {"goals": best("goals"), "assists": best("assists"), "blocks": best("blocks")}
