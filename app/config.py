"""Константы проекта: сезон, ссылки, пути."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

SEASON = "2026/27"
SEASON_TITLE = "Зимняя Песочная Лига"

FANTASY_URL = "https://fantasy.iaroslavexe.art"
TELEGRAM_URL = "https://t.me/beachultimate"
VK_URL = "https://vk.ru/beachultimate"

RULES_URL = "/static/docs/regulations.pdf"

# urlName события этапа на ultisport
STAGE_SLUGS = {
    "1": "zimnyaya-liga-26-27",
    "2": "zimnyaya-liga-26-27-2etap",
    "3": "zimnyaya-liga-26-27-3etap",
    "4": "zimnyaya-liga-26-27-4etap",
}

NAV = [
    {"key": "league", "title": "Лига", "url": "/"},
    {"key": "standings", "title": "Рейтинг", "url": "/standings"},
    {"key": "stages", "title": "Этапы", "url": "/stages"},
    {"key": "stats", "title": "Статистика", "url": "/stats"},
    {"key": "rules", "title": "Регламент", "url": "/rules"},
]
