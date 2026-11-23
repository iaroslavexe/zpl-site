"""Снимок игр этапов с ultisport → app/data/stages.json.

Запуск: python3 scripts/sync_stage_games.py
Структуру (группы, стыки, игры за места) пока не размечаем — только игры по времени.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import STAGE_SLUGS  # noqa: E402
from scripts.ultisport import gql  # noqa: E402

OUT = ROOT / "app" / "data" / "stages.json"
MSK = timezone(timedelta(hours=3))
AVATARS = "https://avatar.ultisport.ru/upload/resized/192_{}"

QUERY = """
query Stage($urlName: String!) {
  event {
    getByURLName(urlName: $urlName) {
      id title startDate
      divisions {
        teams {
          title
          club { avatarId }
        }
        games {
          id scheduledAt status
          homeTeam { title }
          visitorTeam { title }
          homeTeamScore
          visitorTeamScore
        }
      }
    }
  }
}
"""


def msk_time(value: str) -> str:
    # scheduledAt отдаётся по МСК с суффиксом Z — не конвертируем, только режем время
    return value[11:16]


def main() -> None:
    standings = json.loads((OUT.parent / "standings.json").read_text(encoding="utf-8"))
    stages = []
    for stage in standings["stages"]:
        slug = STAGE_SLUGS.get(stage["id"])
        item = {**stage, "games": []}
        if not slug:
            stages.append(item)
            continue
        data = gql(QUERY, {"urlName": slug})
        event = (data.get("data") or {}).get("event", {}).get("getByURLName")
        if not event:
            stages.append(item)
            continue
        games, teams = [], {}
        for division in event.get("divisions") or []:
            games.extend(division.get("games") or [])
            for team in division.get("teams") or []:
                avatar = (team.get("club") or {}).get("avatarId") or ""
                if avatar.startswith("resized/"):
                    avatar = avatar[len("resized/"):]
                if avatar:
                    teams[team["title"]] = AVATARS.format(avatar)
        games.sort(key=lambda g: g["scheduledAt"])
        item["teams"] = teams
        item["games"] = [
            {
                "id": g["id"],
                "time": msk_time(g["scheduledAt"]),
                "home": g["homeTeam"]["title"],
                "visitor": g["visitorTeam"]["title"],
                "home_score": g["homeTeamScore"],
                "visitor_score": g["visitorTeamScore"],
                "status": g["status"],
            }
            for g in games
        ]
        stages.append(item)

    payload = {"season": standings["season"], "synced_at": datetime.now(MSK).isoformat(timespec="minutes"), "stages": stages}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ok: {OUT} | игр по этапам: {[len(s['games']) for s in stages]}")


if __name__ == "__main__":
    main()
