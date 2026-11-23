"""Зачёт: очки за место на этапе → место, сумма, ранжирование."""
from app.services.storage import load

# насколько сильно заливать ячейку: от 1-го места к последнему
_TOP_RGB = (250, 183, 44)     # жёлтый
_LOW_RGB = (59, 69, 87)       # серо-синий


def _tint(place: int, teams: int) -> str:
    t = 1 - (place - 1) / max(teams - 1, 1)
    r = round(_LOW_RGB[0] + (_TOP_RGB[0] - _LOW_RGB[0]) * t)
    g = round(_LOW_RGB[1] + (_TOP_RGB[1] - _LOW_RGB[1]) * t)
    b = round(_LOW_RGB[2] + (_TOP_RGB[2] - _LOW_RGB[2]) * t)
    a = 0.10 + 0.24 * t
    return f"rgba({r}, {g}, {b}, {a:.2f})"


def build() -> dict:
    data = load("standings.json")
    if not data:
        return {"stages": [], "rows": [], "teams_count": 0}

    stages = data["stages"]
    by_place = {points: i + 1 for i, points in enumerate(data["points_by_place"])}
    teams_count = len(data["teams"])

    rows = []
    for team in data["teams"]:
        cells, total, last_points = {}, 0, -1
        for stage in stages:
            points = team["results"].get(stage["id"])
            if points is None:
                cells[stage["id"]] = None
                continue
            place = by_place.get(points)
            cells[stage["id"]] = {
                "place": place,
                "points": points,
                "tint": _tint(place, teams_count) if place else "transparent",
            }
            # тай-брейк считаем по последнему завершённому этапу, а не по лучшему
            if stage.get("status") == "done":
                last_points = points
            if stage.get("counts_in_total", True):
                total += points
        rows.append({**team, "cells": cells, "total": total, "last_points": last_points})

    # тай-брейк: сумма, затем очки последнего завершённого этапа, затем имя
    rows.sort(key=lambda r: (-r["total"], -r["last_points"], r["name"]))
    for index, row in enumerate(rows, 1):
        row["rank"] = index

    return {"stages": stages, "rows": rows, "teams_count": teams_count}
