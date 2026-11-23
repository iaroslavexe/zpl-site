"""Этапы: игры + разметка (группы, стыки, финалы) + таблицы групп."""
from app.services.storage import load


def _group_table(games: list) -> list[dict]:
    stats: dict[str, dict] = {}
    for game in games:
        for name, scored, missed in (
            (game["home"], game["home_score"], game["visitor_score"]),
            (game["visitor"], game["visitor_score"], game["home_score"]),
        ):
            row = stats.setdefault(name, {"team": name, "wins": 0, "losses": 0, "plus": 0, "minus": 0})
            row["plus"] += scored
            row["minus"] += missed
            if scored > missed:
                row["wins"] += 1
            else:
                row["losses"] += 1

    rows = sorted(stats.values(), key=lambda r: (-r["wins"], -(r["plus"] - r["minus"]), r["team"]))
    for place, row in enumerate(rows, 1):
        row["place"] = place
        row["diff"] = row["plus"] - row["minus"]
    return rows


def stage_list() -> list[dict]:
    """Этапы регулярки + финал (он живёт в standings.json, а не в снимке игр)."""
    stages = list(load("stages.json").get("stages", []))
    final = load("standings.json").get("final")
    if final:
        stages.append({
            "id": "final",
            "title": final.get("title", "Финал"),
            "date": final["date"],
            "end_date": final.get("end_date"),
            "place": final.get("place"),
            "games": [],
        })
    return stages


def build(stage_id: str) -> dict:
    data = load("stages.json")
    layouts = load("stage_layouts.json")
    stages = stage_list()
    stage = next((s for s in stages if s["id"] == stage_id), None)
    if not stage:
        return {"stage": None, "blocks": [], "stages": stages}

    teams = stage.get("teams", {})
    games = {g["id"]: g for g in stage.get("games", [])}
    layout = layouts.get(stage_id, {"blocks": []})

    blocks = []
    for block in layout.get("blocks", []):
        items = []
        for gid in block.get("games", []):
            game = games.get(gid)
            if not game:
                continue
            items.append({
                **game,
                "home_avatar": teams.get(game["home"]),
                "visitor_avatar": teams.get(game["visitor"]),
            })
        entry = {**block, "games": items}
        if block.get("type") == "group" and items:
            entry["table"] = _group_table(items)
        blocks.append(entry)

    return {
        "stage": stage,
        "stages": stages,
        "blocks": blocks,
        "teams": teams,
        "games_count": len(stage.get("games", [])),
    }
