"""Черновик разметки этапа: группы — автоматом, плей-офф — по порядку игр.

Запуск: python3 scripts/draft_layout.py
Результат: app/data/stage_layouts.json — его правим руками, скрипт только черновик.
"""
import json
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "app" / "data"

GROUP_ROUNDS = 3  # в групповом этапе каждый играет по 3 игры
GROUPS_LETTERS = "ABCDEFGH"

# порядок, в котором игры реально шли в расписании — по нему раздаём игры блокам
PLAYOFF_ASSIGN = [
    ("Стыки за 1–6 места", 2, ""),
    ("1/2 за 7–10 места", 2, ""),
    ("Игра за 11 место", 1, ""),
    ("1/2 за 1–4 места", 2, ""),
    ("Игра за 5 место", 1, ""),
    ("Игра за 7 место", 1, ""),
    ("Игра за 9 место", 1, ""),
    ("Финал", 1, ""),
    ("Игра за 3 место", 1, ""),
]

# порядок показа на странице — по спортивной логике, а не по времени
PLAYOFF_DISPLAY = [
    "Стыки за 1–6 места",
    "1/2 за 7–10 места",
    "1/2 за 1–4 места",
    "Игра за 11 место",
    "Игра за 9 место",
    "Игра за 7 место",
    "Игра за 5 место",
    "Игра за 3 место",
    "Финал",
]


def split_groups(games: list) -> list[list]:
    """Связные компоненты графа соперников — так делится групповой этап."""
    adj = defaultdict(set)
    for game in games:
        a, b = game["home"], game["visitor"]
        adj[a].add(b)
        adj[b].add(a)

    seen, groups = set(), []
    for team in adj:
        if team in seen:
            continue
        stack, comp = [team], set()
        while stack:
            node = stack.pop()
            if node in comp:
                continue
            comp.add(node)
            stack.extend(adj[node] - comp)
        seen |= comp
        groups.append(sorted(comp))
    return groups


def _norm(name: str) -> str:
    return name.lower().replace("’", "'").replace("ё", "е").strip()


def power_pool(groups: list[list], stage_id: str, standings: dict) -> list[list]:
    """Группа A — пауэр-пул: четвёрка сильнейших по зачёту прошлого этапа."""
    order = [s["id"] for s in standings.get("stages", [])]
    if stage_id not in order or order.index(stage_id) == 0:
        return groups
    previous = order[order.index(stage_id) - 1]

    points = {}
    for team in standings.get("teams", []):
        value = team.get("results", {}).get(previous)
        if value is not None:
            points[_norm(team["name"])] = value

    top = [name for name, _ in sorted(points.items(), key=lambda kv: -kv[1])[:4]]
    if not top:
        return groups

    def hits(group):
        return len({_norm(t) for t in group} & set(top))

    best = max(range(len(groups)), key=lambda i: hits(groups[i]))
    if hits(groups[best]) < 3:
        return groups
    return [groups[best]] + [g for i, g in enumerate(groups) if i != best]


def build(stage: dict, standings: dict | None = None) -> dict:
    games = stage["games"]
    if not games:
        return {"blocks": []}

    teams_count = len({g["home"] for g in games} | {g["visitor"] for g in games})
    group_games_count = GROUP_ROUNDS * (teams_count // 2)
    head, tail = games[:group_games_count], games[group_games_count:]

    groups = split_groups(head)
    if standings:
        groups = power_pool(groups, stage["id"], standings)
    blocks = []
    grouped_ids, team_block = set(), {}

    for index, group in enumerate(groups):
        letter = GROUPS_LETTERS[index]
        ids = [g["id"] for g in head if g["home"] in group and g["visitor"] in group]
        grouped_ids.update(ids)
        for team in group:
            team_block[team] = letter
        blocks.append({
            "title": f"Группа {letter}",
            "note": "Пауэр пул" if index == 0 else "",
            "type": "group",
            "teams": group,
            "games": ids,
        })

    # остатки группового блока (если разбиение не идеальное) кладём в плей-офф
    rest = [g for g in head if g["id"] not in grouped_ids] + tail

    cursor = 0
    for title, count, note in PLAYOFF_ASSIGN:
        chunk = [g["id"] for g in rest[cursor:cursor + count]]
        cursor += count
        if not chunk:
            continue
        blocks.append({"title": title, "note": note, "type": "round", "games": chunk})

    if cursor < len(rest):
        blocks.append({
            "title": "Прочее",
            "type": "round",
            "games": [g["id"] for g in rest[cursor:]],
        })

    groups = [b for b in blocks if b.get("type") == "group"]
    others = [b for b in blocks if b.get("type") != "group"]
    rank = {title: i for i, title in enumerate(PLAYOFF_DISPLAY)}
    others.sort(key=lambda b: rank.get(b["title"], len(rank)))
    return {"blocks": groups + others}


def main() -> None:
    stages = json.loads((DATA / "stages.json").read_text(encoding="utf-8"))["stages"]
    standings = json.loads((DATA / "standings.json").read_text(encoding="utf-8"))
    layout = {
        stage["id"]: build(stage, standings)
        for stage in stages
        if stage.get("games")
    }
    path = DATA / "stage_layouts.json"
    path.write_text(json.dumps(layout, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for sid, data in layout.items():
        print(f"этап {sid}: блоков {len(data['blocks'])}, игр {sum(len(b['games']) for b in data['blocks'])}")
        for block in data["blocks"]:
            print(f"   {block['title']:22s} игр: {len(block['games'])}")


if __name__ == "__main__":
    main()
