"""Составы этапов с ultisport → app/data/rosters.json.

Нужен, чтобы понимать, за какую команду игрок играл на конкретном этапе.
Запуск: python3 scripts/sync_rosters.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import STAGE_SLUGS  # noqa: E402
from app.services.teams import normalize  # noqa: E402
from scripts.ultisport import gql  # noqa: E402

DATA = ROOT / "app" / "data"

QUERY = """
query Roster($urlName: String!) {
  event {
    getByURLName(urlName: $urlName) {
      divisions { teams { title players { account { firstName lastName } } } }
    }
  }
}
"""


def main() -> None:
    rosters = {}
    for stage_id, slug in STAGE_SLUGS.items():
        data = gql(QUERY, {"urlName": slug})
        event = (data.get("data") or {}).get("event", {}).get("getByURLName")
        if not event:
            continue
        stage = {}
        for division in event.get("divisions") or []:
            for team in division.get("teams") or []:
                title = normalize(team.get("title"))
                for player in team.get("players") or []:
                    account = player.get("account") or {}
                    name = f"{account.get('firstName', '')} {account.get('lastName', '')}".strip()
                    if name:
                        stage[name] = title
        if stage:
            rosters[stage_id] = stage
        print(f"этап {stage_id}: {len(stage)} игроков")

    path = DATA / "rosters.json"
    path.write_text(json.dumps(rosters, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ok:", path)


if __name__ == "__main__":
    main()
