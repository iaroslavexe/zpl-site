"""Сборка статической версии сайта в dist/.

Запуск: python -m app.build
Cloudflare Pages раздаёт только готовые файлы, поэтому рендерим страницы заранее.
"""
import hashlib
import json
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app import assets, views
from app.config import SITE_URL, STATIC_DIR, TEMPLATES_DIR

DIST = Path(__file__).resolve().parent.parent / "dist"

ARCHIVE_PAGES = {
    "archive/index.html": views.archive_landing,
    "archive/teams/index.html": lambda: views.archive_catalog("teams"),
    "archive/players/index.html": lambda: views.archive_catalog("players"),
    "archive/awards/index.html": lambda: views.archive_catalog("awards"),
    "archive/stages/index.html": lambda: views.archive_catalog("stages"),
    "archive/seasons/index.html": lambda: views.archive_catalog("seasons"),
    "archive/entity.html": views.archive_entity,
}

PAGES = {
    "index.html": views.league,
    "standings.html": views.standings_page,
    "stages.html": views.stages,
    "stats.html": views.stats,
    "rules.html": views.rules,
    "404.html": views.not_found,
}

HEADERS = """# Cloudflare Pages: заголовки
/static/fonts/*
  Cache-Control: public, max-age=31536000, immutable
/static/*
  Cache-Control: public, max-age=31536000, immutable
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
"""

ROBOTS = """User-agent: *
Allow: /

Sitemap: {site}/sitemap.xml
"""

SITEMAP_PAGES = ["/", "/standings", "/stages", "/stats", "/rules",
                 "/archive/", "/archive/seasons/", "/archive/stages/",
                 "/archive/teams/", "/archive/players/", "/archive/awards/"]


def main() -> None:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html"]),
    )
    env.globals["static_url"] = assets.url

    # простая проверка целостности клиентского рендерера архива
    js = (STATIC_DIR / "js" / "archive-app.js").read_text(encoding="utf-8")
    for required in ("function renderTeam", "function renderPlayer", "function renderStage",
                     "function renderGame", "function render404"):
        if required not in js:
            raise SystemExit(f"archive-app.js: пропала {required}")

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    # статика: копируем и переименовываем css/js с хешем содержимого в имени,
    # чтобы CDN и браузеры не отдавали старые версии из вечного кэша
    shutil.copytree(STATIC_DIR, DIST / "static")
    manifest = {}
    for suffix in (".css", ".js"):
        for path in sorted((DIST / "static").rglob(f"*{suffix}")):
            digest = hashlib.sha1(path.read_bytes()).hexdigest()[:8]
            hashed = path.with_name(f"{path.stem}.{digest}{path.suffix}")
            path.rename(hashed)
            manifest[str(path.relative_to(DIST))] = str(hashed.relative_to(DIST))
    assets.set_manifest(manifest)

    all_pages = dict(PAGES)
    all_pages.update(ARCHIVE_PAGES)

    for filename, page in all_pages.items():
        name, context = page()
        html = env.get_template(name).render(**context)
        target = DIST / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        print(f"  {filename:28} {len(html) / 1024:6.0f} КБ")

    shutil.copy(Path(__file__).resolve().parent / "data" / "archive" / "archive.json",
                DIST / "archive" / "data.json")

    # Карточки архива: один и тот же shell на каждый путь, чтобы не было редиректов
    shell = (DIST / "archive" / "entity.html").read_text(encoding="utf-8")
    bundle = json.loads((Path(__file__).resolve().parent / "data" / "archive" / "archive.json")
                        .read_text(encoding="utf-8"))
    entity_paths = []
    for team in bundle["teams"]:
        entity_paths.append(f"archive/team/{team['id']}")
    for player in bundle["players"]:
        entity_paths.append(f"archive/player/{player['id']}")
    for stage in bundle["stages"]:
        entity_paths.append(f"archive/stage/{stage['slug']}")
    for game in bundle["games"]:
        entity_paths.append(f"archive/game/{game['id']}")

    for path in entity_paths:
        target = DIST / path / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(shell, encoding="utf-8")
    (DIST / "_headers").write_text(HEADERS, encoding="utf-8")
    (DIST / "_redirects").write_text(
        "",
        encoding="utf-8",
    )
    (DIST / "robots.txt").write_text(ROBOTS.format(site=SITE_URL), encoding="utf-8")

    urls = "".join(f"  <url><loc>{SITE_URL}{path}</loc></url>\n" for path in SITEMAP_PAGES)
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n",
        encoding="utf-8",
    )

    total = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file())
    print(f"готово: {DIST} · {total / 1048576:.1f} МБ")


if __name__ == "__main__":
    main()
