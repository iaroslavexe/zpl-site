"""Сборка статической версии сайта в dist/.

Запуск: python -m app.build
Cloudflare Pages раздаёт только готовые файлы, поэтому рендерим страницы заранее.
"""
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app import views
from app.config import SITE_URL, STATIC_DIR, TEMPLATES_DIR

DIST = Path(__file__).resolve().parent.parent / "dist"

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
  Cache-Control: public, max-age=604800
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
"""

ROBOTS = """User-agent: *
Allow: /

Sitemap: {site}/sitemap.xml
"""

SITEMAP_PAGES = ["/", "/standings", "/stages", "/stats", "/rules"]


def main() -> None:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html"]),
    )

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    for filename, page in PAGES.items():
        name, context = page()
        html = env.get_template(name).render(**context)
        (DIST / filename).write_text(html, encoding="utf-8")
        print(f"  {filename:18} {len(html) / 1024:6.0f} КБ")

    shutil.copytree(STATIC_DIR, DIST / "static")
    (DIST / "_headers").write_text(HEADERS, encoding="utf-8")
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
