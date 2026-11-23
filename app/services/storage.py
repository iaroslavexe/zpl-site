"""Чтение JSON-снимков из app/data. Файлы меняются только sync-скриптом."""
import json
from functools import lru_cache

from app.config import DATA_DIR


@lru_cache(maxsize=None)
def load(name: str) -> dict:
    path = DATA_DIR / name
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def reload() -> None:
    load.cache_clear()
