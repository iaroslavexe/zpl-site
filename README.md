# zpl-main-site

Сайт лиги ЗПЛ: витрина сезона, зачёт, этапы, статистика, регламент.

## Стек

Python 3.12 + FastAPI + Jinja2, ванильный CSS/JS, без сборки.
Данные — JSON-снимки в `app/data/`, база не нужна.

## Локальный запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Открыть http://127.0.0.1:8000

## Шрифты

Шрифты лежат локально в `app/static/fonts` (Jost, Oswald, Unbounded), подключены через
`app/static/css/fonts.css`. Нужны, чтобы заголовок не «переодевался» со запасного шрифта
при загрузке и чтобы не зависеть от Google Fonts.

Пересобрать (если меняли набор начертаний):

```bash
python3 scripts/vendor_fonts.py
```

## Структура

```
app/
├── main.py              # приложение, монтирование роутеров и статики
├── config.py            # сезон, ссылки, навигация
├── routers/pages.py     # роуты страниц
├── services/
│   ├── storage.py       # чтение JSON с кэшем
│   ├── stats.py         # статистика игроков: топы, разбивка по этапам
│   ├── stages.py        # этапы: блоки, таблицы групп, составы
│   ├── streams.py       # трансляции ВК
│   ├── teams.py         # канонические названия команд
│   └── standings.py     # зачёт: место из очков, суммы, ранжирование, заливка
├── data/
│   ├── standings.json   # очки команд по этапам (правится руками)
│   └── stages.json      # игры этапов (генерит scripts/sync_stage_games.py)
├── templates/           # base.html + pages/
└── static/              # css/{tokens,base,layout,components,pages}.css, js/app.js, docs/
```

## Данные

- **Зачёт** — `app/data/standings.json`: сетка очков за места (`points_by_place`) и очки команд по этапам.
  Место на этапе вычисляется из очков, сумма и ранжирование — в `services/standings.py`.
- **Этапы** — `scripts/sync_stage_games.py` тянет игры с ultisport по `urlName` этапа.
  Запуск вручную после этапа: `python3 scripts/sync_stage_games.py`.

## Статистика игроков

Гибрид: снимок в сборке + живые данные в браузере.

- `app/data/player_stats.json` — снимок, попадает в HTML при сборке (работает без JS).
- В браузере `static/js/stats.js` запрашивает `https://fantasy.iaroslavexe.art/api/league/stats`
  (публичный, CORS `*`) и подменяет цифры на свежие. Не ответил — остаётся снимок.
- Источник данных: таблица `player_stats` в фэнтези (голы/ассисты из протоколов, блоки вносятся вручную).

Составы по этапам (кто за какую команду играл) — `scripts/sync_rosters.py` пишет `app/data/rosters.json`.
Без него в таблице показывается только текущая команда игрока.

```bash
python3 scripts/sync_rosters.py
```

Обновить снимок перед сборкой:

```bash
curl -s https://fantasy.iaroslavexe.art/api/league/stats -o app/data/player_stats.json
```

## Что дальше

- разметка этапа: группы, стыки, игры за места;
- статистика игроков (источник — фэнтези или расчёт из действий ultisport);
- PDF регламента (сжать перед загрузкой);
- страницы «Тест» и «Дух»;
- ретроспектива сезонов.
