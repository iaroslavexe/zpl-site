"""Точка входа: собирает приложение из роутеров."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import STATIC_DIR
from app.routers import pages

app = FastAPI(title="ЗПЛ — Зимняя Песочная Лига")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(pages.router)
