"""Названия команд: разные написания → одно каноническое (как в standings.json)."""
from app.services.storage import load


def normalize(title: str | None) -> str:
    if not title:
        return ""
    aliases = load("team_aliases.json")
    key = title.replace("’", "'").strip().lower()
    return aliases.get(key, title)
