"""Скачивает нужные шрифты Google Fonts в app/static/fonts и собирает fonts.css.

Зачем: без внешних запросов заголовок не «переодевается» с запасного шрифта
на нужный при загрузке. Запуск: python3 scripts/vendor_fonts.py

Jost — вариативный: Google отдаёт один и тот же файл на все начертания,
поэтому он подключается диапазоном 400–700, а не четырьмя копиями.
"""
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "app" / "static" / "fonts"
CSS_OUT = ROOT / "app" / "static" / "css" / "fonts.css"

FAMILIES = "family=Jost:wght@400;500;600;700&family=Oswald:wght@600&family=Unbounded:wght@600&display=swap"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
KEEP = ("cyrillic", "latin")
# у вариативных шрифтов начертания идут диапазоном
WEIGHT_RANGE = {"Jost": "400 700"}


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def main() -> None:
    FONTS.mkdir(parents=True, exist_ok=True)
    for old in FONTS.glob("*.woff2"):
        old.unlink()

    css = fetch(f"https://fonts.googleapis.com/css2?{FAMILIES}").decode()
    blocks = re.findall(r"/\*\s*([a-z-]+)\s*\*/\s*(@font-face\s*\{[^}]*\})", css)

    seen: dict[str, str] = {}
    out = ["/* Локальные копии шрифтов Google Fonts (OFL). Сгенерировано scripts/vendor_fonts.py */"]

    for subset, block in blocks:
        if subset not in KEEP:
            continue
        family = re.search(r"font-family:\s*'([^']+)'", block).group(1)
        weight = re.search(r"font-weight:\s*(\d+)", block).group(1)
        url = re.search(r"url\((https://[^)]+\.woff2)\)", block).group(1)

        slug = family.lower().replace(" ", "-")
        name = seen.get(url) or (
            f"{slug}-{subset}.woff2" if family in WEIGHT_RANGE else f"{slug}-{weight}-{subset}.woff2"
        )
        if url not in seen:
            (FONTS / name).write_bytes(fetch(url))
            seen[url] = name

        block = block.replace(url, f"/static/fonts/{name}")
        block = re.sub(r"font-display:\s*\w+;", "font-display: swap;", block)
        if family in WEIGHT_RANGE:
            block = re.sub(r"font-weight:\s*\d+;", f"font-weight: {WEIGHT_RANGE[family]};", block)
        out.append(f"/* {family} · {subset} */\n{block}")

    CSS_OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    total = sum(f.stat().st_size for f in FONTS.iterdir())
    print(f"файлов: {len(list(FONTS.iterdir()))}, всего {total / 1024:.0f} КБ → {CSS_OUT}")


if __name__ == "__main__":
    main()
