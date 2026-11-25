"""Версионирование статики: /static/css/pages.css?v=<hash содержимого>."""
import hashlib
from functools import lru_cache
from pathlib import Path

from app.config import STATIC_DIR

_CACHE: dict = {}
_MANIFEST: dict = {}


def set_manifest(mapping: dict) -> None:
    """Сборка кладёт сюда карту «исходный путь → файл с хешем в имени»."""
    _MANIFEST.clear()
    _MANIFEST.update(mapping)


def version(rel_path: str) -> str:
    path = Path(STATIC_DIR) / rel_path
    try:
        stat = path.stat()
    except FileNotFoundError:
        return "0"

    key = (str(path), stat.st_mtime_ns, stat.st_size)
    if key not in _CACHE:
        _CACHE[key] = hashlib.sha1(path.read_bytes()).hexdigest()[:8]
    return _CACHE[key]


def url(path: str) -> str:
    """/static/js/app.js → /static/js/app.1a2b3c4d.js (или ?v= в dev-режиме)."""
    rel = path[len("/static/"):] if path.startswith("/static/") else path
    key = f"static/{rel}"
    if key in _MANIFEST:
        return "/" + _MANIFEST[key]
    return f"/static/{rel}?v={version(rel)}"
