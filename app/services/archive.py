"""Архив лиги: сезоны, этапы, команды, игроки, игры (только завершённые сезоны)."""
from functools import lru_cache
from pathlib import Path

from app.config import DATA_DIR
from app.services.storage import load

ARCHIVE_DIR = Path(DATA_DIR) / "archive"
SEASONS = ("2021/22", "2022/23", "2023/24", "2024/25", "2025/26")


def _load(name: str) -> list:
    path = ARCHIVE_DIR / f"{name}.json"
    return load(f"archive/{name}.json") if path.exists() else []


AWARD_TYPES = {
    "season_mvp": {"title": "MVP сезона"},
    "season_defense": {"title": "MVP сезона · защита"},
    "regular_mvp": {"title": "MVP регулярного сезона"},
    "regular_defense": {"title": "MVP регулярного сезона · защита"},
    "regular_mvp_central": {"title": "MVP регулярного сезона · Центральный"},
    "regular_defense_central": {"title": "MVP регулярного сезона · защита · Центральный"},
    "regular_mvp_spb": {"title": "MVP регулярного сезона · Северо-западный"},
    "regular_defense_spb": {"title": "MVP регулярного сезона · защита · Северо-западный"},
    "final_mvp": {"title": "MVP финала"},
    "final_defense": {"title": "MVP финала · защита"},
    "final_mid_mvp": {"title": "MVP финала Mid", "quiet": True},
    "final_mid_defense": {"title": "MVP финала Mid · защита", "quiet": True},
    "offense": {"title": "Лучший в атаке"},
    "defense": {"title": "Лучший в защите"},
    "spirit_player": {"title": "Дух игры"},
    "spirit_team": {"title": "Дух игры", "team": True},
}


@lru_cache(maxsize=1)
def awards() -> list:
    """Личные и командные награды: сезон, тип, победители."""
    raw = _load("awards")
    players = {p["id"]: p for p in _load("players")}
    teams = {t["id"]: t for t in _load("teams")}
    result = []
    for item in raw:
        meta = AWARD_TYPES.get(item["type"], {"title": item["type"]})
        result.append({
            "season": item["season"],
            "type": item["type"],
            "title": meta["title"],
            "team": meta.get("team", False),
            "quiet": meta.get("quiet", False),
            "players": [players[p] for p in item.get("players", []) if p in players],
            "teams": [teams[t] for t in item.get("teams", []) if t in teams],
        })
    return result


@lru_cache(maxsize=1)
def awards_by_player() -> dict:
    grouped: dict = {}
    for award in awards():
        for player in award["players"]:
            grouped.setdefault(player["id"], []).append(award)
    return grouped


def regular_mvp(season: str) -> list:
    for award in awards():
        if award["season"] == season and award["type"] == "regular_mvp":
            return award["players"]
    return []


def season_head_award(season: str):
    """Главная награда сезона: «MVP сезона» или, с 24/25, «MVP регулярного сезона»."""
    items = [a for a in awards() if a["season"] == season]
    for wanted in ("season_mvp", "regular_mvp_central", "regular_mvp"):
        for award in items:
            if award["type"] == wanted:
                return award
    return None


def season_heads(season: str) -> list:
    award = season_head_award(season)
    return award["players"] if award else []


@lru_cache(maxsize=1)
def data() -> dict:
    stages = _load("stages")
    teams = _load("teams")
    players = _load("players")
    games = _load("games")

    stage_by_id = {s["id"]: s for s in stages}
    team_by_id = {t["id"]: t for t in teams}
    player_by_id = {p["id"]: p for p in players}

    games_by_stage: dict[str, list] = {}
    for game in games:
        game["home_name"] = team_by_id.get(game["home"], {}).get("name", game["home"])
        game["away_name"] = team_by_id.get(game["away"], {}).get("name", game["away"])
        games_by_stage.setdefault(game["stage"], []).append(game)

    for stage in stages:
        stage["teams"] = [[tid, p] for tid, p, _ in stage["places"]]
        stage["game_list"] = sorted(games_by_stage.get(stage["id"], []), key=lambda g: g["id"])

    return {
        "stages": stages,
        "stage_by_id": stage_by_id,
        "teams": teams,
        "team_by_id": team_by_id,
        "players": players,
        "player_by_id": player_by_id,
        "games": games,
        "game_by_id": {g["id"]: g for g in games},
    }


def summary() -> dict:
    d = data()
    return {
        "seasons": len(SEASONS),
        "stages": len(d["stages"]),
        "teams": len(d["teams"]),
        "players": len(d["players"]),
        "games": len(d["games"]),
        "goals": sum((g["hs"] or 0) + (g["vs"] or 0) for g in d["games"]),
    }


def champions() -> list[dict]:
    """Чемпион сезона: финал, а если его не было — лучшая команда по этапам."""
    out = []
    d = data()
    for season in SEASONS:
        stages = [s for s in d["stages"] if s["season"] == season]
        final = next((s for s in stages if "финал" in s["title"].lower()), None)
        row = {"season": season, "teams": [], "stage": final}

        if final:
            rows = sorted(final["places"], key=lambda r: r[1])
            elite = [r for r in rows if not r[2] or r[2] != "Mid"]
            row["teams"] = [(d["team_by_id"].get(t, {}).get("name", t), p, div)
                            for t, p, div in elite[:3]]
        else:
            # без финала: больше побед на этапах, затем лучше среднее место
            stats: dict[str, dict] = {}
            for s in stages:
                for tid, place, _division in s["places"]:
                    item = stats.setdefault(tid, {"gold": 0, "places": []})
                    item["gold"] += 1 if place == 1 else 0
                    item["places"].append(place)
            best = sorted(stats.items(), key=lambda kv: (-kv[1]["gold"], sum(kv[1]["places"]) / len(kv[1]["places"])))
            row["teams"] = [(d["team_by_id"].get(tid, {}).get("name", tid), None, None)
                            for tid, _ in best[:3]]
        out.append(row)
    return out


def team(team_id: str) -> dict | None:
    return data()["team_by_id"].get(team_id)


def player(player_id: str) -> dict | None:
    return data()["player_by_id"].get(player_id)


def stage(slug: str) -> dict | None:
    return next((s for s in data()["stages"] if s["slug"] == slug), None)


def game(game_id: int) -> dict | None:
    return data()["game_by_id"].get(game_id)
