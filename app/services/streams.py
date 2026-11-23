"""Трансляции этапов: ссылки на записи ВКонтакте.

Встраивание плеера ВК требует hash из кода «Экспортировать» — без него ВК
показывает «Видео недоступно» анонимным зрителям. Поэтому пока карточки-ссылки.
"""
from app.services.storage import load


def build() -> dict:
    data = load("streams.json")
    return {**data, "clips": data.get("clips", [])}
