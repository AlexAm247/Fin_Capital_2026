#!/usr/bin/env python3
"""Build wiki pages from tools/chat.jsonl according to page specifications.

Usage:
    python3 tools/build_wiki.py              # full rebuild of quote blocks
    python3 tools/build_wiki.py --since 2026-01-01  # only messages after date

The script preserves hand-written sections (everything outside the autogen
markers). On first run it creates a skeleton page with placeholders.

Autogen markers in each page:
    <!-- autogen:quotes:start -->
    ...generated quotes...
    <!-- autogen:quotes:end -->
"""

from __future__ import annotations

import argparse
import json
import re
import textwrap
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "tools" / "chat.jsonl"
WIKI = ROOT / "wiki"

TODAY = date.today().isoformat()

# ── RU hard-exclude terms ─────────────────────────────────────────────
RU_HARD_TERMS = [
    "рубл", "офз", "мосбирж", "ммвб", "сбербанк", "газпром", "лукойл",
    "роснефт", "норникел", "втб", "иис", "цб рф", "банка росс",
    "ключевая ставка",
]


def ru_score(text: str) -> int:
    lo = text.lower()
    return sum(1 for t in RU_HARD_TERMS if t in lo)


# ── Page specifications ───────────────────────────────────────────────
# Each spec: (category, slug, title, type, tags, keywords, max_quotes)

PAGE_SPECS: list[dict] = [
    # ── concepts ──────────────────────────────────────────────────────
    {
        "cat": "concepts", "slug": "philosophy-long-term",
        "title": "Философия долгосрочного инвестирования",
        "type": "concept",
        "tags": ["философия", "долгосрочность", "дисциплина"],
        "kw": [
            "долгосроч", "дисциплин", "терпен", "горизонт", "сложный процент",
            "compounding", "не казино", "процесс", "время в рынке",
            "time in the market",
        ],
        "max": 30,
    },
    {
        "cat": "concepts", "slug": "behavioral-traps",
        "title": "Поведенческие ловушки и когнитивные искажения",
        "type": "concept",
        "tags": ["поведенческие финансы", "психология", "ошибки"],
        "kw": [
            "поведенческ", "психолог", "когнитивн", "искажени", "эмоци",
            "страх", "жадност", "fomo", "паник", "эйфори", "иллюзи",
            "канеман", "ловушк", "bias", "толп", "стадн",
        ],
        "max": 30,
    },
    {
        "cat": "concepts", "slug": "advisor-commissions",
        "title": "Комиссии советников и дорогие продукты",
        "type": "concept",
        "tags": ["советники", "комиссии", "продукты", "конфликт интересов"],
        "kw": [
            "советник", "консультант", "комисси", "впарив", "управляющ",
            "структурн", "unit-linked", "unit linked", "пиф",
            "конфликт интерес", "продавец", "вознагражден",
            "ter ", "комиссионны", "навязыва",
        ],
        "max": 30,
    },
    {
        "cat": "concepts", "slug": "asset-allocation",
        "title": "Asset allocation — распределение активов",
        "type": "concept",
        "tags": ["портфель", "аллокация", "распределение"],
        "kw": [
            "аллокаци", "allocation", "распределен актив", "доля",
            "вес в портфел", "пропорци", "класс актив",
            "asset class", "multi-asset", "мультиактив",
        ],
        "max": 30,
    },
    {
        "cat": "concepts", "slug": "rebalancing",
        "title": "Ребалансировка портфеля",
        "type": "concept",
        "tags": ["ребалансировка", "портфель", "дисциплина"],
        "kw": [
            "ребаланс", "rebalance", "перебаланс", "фиксир прибыл",
            "фиксиру прибыл", "продавать на росте", "докупать на просадк",
            "возврат к целев", "target weight",
        ],
        "max": 25,
    },
    {
        "cat": "concepts", "slug": "risk-management",
        "title": "Управление рисками и волатильность",
        "type": "concept",
        "tags": ["риск", "волатильность", "просадки", "хеджирование"],
        "kw": [
            "волатильн", "просадк", "drawdown", "хедж", "hedge",
            "риск-менеджм", "управлени рис", "stop-loss", "стоп-лосс",
            "vix", "корреляци", "диверсифик",
        ],
        "max": 30,
    },
    {
        "cat": "concepts", "slug": "goals-and-fire",
        "title": "Финансовые цели, пенсия и FIRE",
        "type": "concept",
        "tags": ["цели", "пенсия", "FIRE", "накопления"],
        "kw": [
            "пенси", "финансов цел", "финансовые цел", "финансовой цел",
            "накоплен", "fire", "финансовая независ", "финансовой независ",
            "подушк безопасн", "сбережени", "горизонт планиров",
        ],
        "max": 25,
    },
    {
        "cat": "concepts", "slug": "books-and-education",
        "title": "Книги, ресурсы и образование инвестора",
        "type": "concept",
        "tags": ["книги", "образование", "ресурсы"],
        "kw": [
            "книг", "почитать", "автор пиш", "рекоменду", "талеб",
            "talib", "богл", "bogle", "грэм", "graham", "баффет",
            "buffett", "далио", "dalio", "ray dalio",
        ],
        "max": 25,
    },
    # ── entities ──────────────────────────────────────────────────────
    {
        "cat": "entities", "slug": "sp500-us-stocks",
        "title": "S&P 500 и американские акции",
        "type": "entity",
        "tags": ["S&P 500", "акции", "США", "Nasdaq"],
        "kw": [
            "s&p", "s & p", "sp500", "s&p 500", "s&p-500", "nasdaq",
            "dow ", "nyse", "apple", "microsoft", "amazon", "tesla",
            "nvidia", "meta ", "google", "alphabet", "netflix",
            "fang", "faang", "mag", "magnificent", "buyback", "байбэк",
            "американск акци", "американского рынк",
        ],
        "max": 35,
    },
    {
        "cat": "entities", "slug": "etfs",
        "title": "ETF и индексные фонды",
        "type": "entity",
        "tags": ["ETF", "индексные фонды", "Vanguard"],
        "kw": [
            " etf", "etf ", "etf.", "etf,", "бпиф", "finex",
            "vanguard", "ishares", "spdr", "qqq", "spy ", " vti",
            "voo ", "индексн фонд", "биржев фонд",
        ],
        "max": 35,
    },
    {
        "cat": "entities", "slug": "gold",
        "title": "Золото и драгметаллы",
        "type": "entity",
        "tags": ["золото", "GLD", "драгметаллы", "хедж"],
        "kw": [
            "золот", "gold", "gld", "драгметалл", "серебр", "silver",
            "gdx", "золотодобытч",
        ],
        "max": 35,
    },
    {
        "cat": "entities", "slug": "bitcoin-crypto",
        "title": "Биткоин и криптовалюты",
        "type": "entity",
        "tags": ["биткоин", "крипто", "блокчейн"],
        "kw": [
            "биткоин", "биткойн", "bitcoin", "btc", "эфириум",
            "ethereum", "eth ", " eth", "крипто", "блокчейн",
            "альткоин", "стейблкоин",
        ],
        "max": 35,
    },
    {
        "cat": "entities", "slug": "us-treasuries",
        "title": "Казначейские облигации США (Treasuries)",
        "type": "entity",
        "tags": ["treasuries", "облигации", "доходность", "ФРС"],
        "kw": [
            "treasury", "treasuries", "трежер", "казначейск",
            "us10", "10-лет", "доходност облигац",
            "бонд", "купон", "кривая доходн",
            "yield", "duration", "дюраци",
        ],
        "max": 30,
    },
    {
        "cat": "entities", "slug": "oil-commodities",
        "title": "Нефть, газ и сырьевые товары",
        "type": "entity",
        "tags": ["нефть", "commodities", "ОПЕК", "сырьё"],
        "kw": [
            "нефт", "brent", "wti", "опек", "opec",
            "коммодит", "commodity", "сырь", "медь", "copper",
        ],
        "max": 25,
    },
    {
        "cat": "entities", "slug": "emerging-markets",
        "title": "Развивающиеся рынки и Китай",
        "type": "entity",
        "tags": ["Китай", "EM", "развивающиеся рынки"],
        "kw": [
            "китай", "китайск", "гонконг", "hong kong",
            "emerging", "развивающ", "индия", "бразили", "юань",
            "em ", " em,",
        ],
        "max": 25,
    },
    # ── theses ────────────────────────────────────────────────────────
    {
        "cat": "theses", "slug": "active-mgmt-passive-instruments",
        "title": "Активное управление пассивными инструментами",
        "type": "thesis",
        "tags": ["пассивное", "активное", "ETF", "тактика"],
        "kw": [
            "пассив", "активн управлени", "активного управлени",
            "индексн фонд", "индексного фонд", "богл", "bogle",
            "активное управление пассивн",
        ],
        "max": 25,
    },
    {
        "cat": "theses", "slug": "gold-as-portfolio-hedge",
        "title": "Золото как стратегический хедж портфеля",
        "type": "thesis",
        "tags": ["золото", "хедж", "портфель"],
        "kw": [
            "золот", "gold", "gld", "хедж", "hedge",
            "страхов", "безопасн гаван", "safe haven",
        ],
        "max": 25,
    },
    {
        "cat": "theses", "slug": "dont-time-the-market",
        "title": "Не пытайся таймить рынок",
        "type": "thesis",
        "tags": ["тайминг", "дисциплина", "ошибки"],
        "kw": [
            "тайминг", "timing", "time the market",
            "предсказать", "предсказыва", "прогноз",
            "угадать дно", "поймать дно", "пропустить рост",
        ],
        "max": 25,
    },
    {
        "cat": "theses", "slug": "volatility-is-opportunity",
        "title": "Волатильность — не враг, а возможность",
        "type": "thesis",
        "tags": ["волатильность", "возможность", "просадки"],
        "kw": [
            "волатильн", "просадк", "коррекци", "возможност",
            "покупать на страх", "жадничай когда", "buy the dip",
            "скидк", "распродаж",
        ],
        "max": 25,
    },
    # ── timeline ──────────────────────────────────────────────────────
    {
        "cat": "timeline", "slug": "2020-covid-crash",
        "title": "2020: COVID-крах и восстановление",
        "type": "timeline",
        "tags": ["COVID", "2020", "кризис", "ФРС"],
        "kw": [
            "covid", "ковид", "пандеми", "коронавир", "карантин",
            "локдаун", "lockdown",
        ],
        "date_from": "2020-01-01",
        "date_to": "2020-12-31",
        "max": 35,
    },
    {
        "cat": "timeline", "slug": "2022-macro-shock",
        "title": "2022: ужесточение ФРС, обвал tech, медвежий рынок",
        "type": "timeline",
        "tags": ["2022", "ФРС", "ставки", "медвежий рынок"],
        "kw": [
            "фрс", "fed ", " fed", "повыш ставк", "повышени ставк",
            "ужесточен", "tightening", "медвеж",
            "bear market", "инфляц",
        ],
        "date_from": "2022-01-01",
        "date_to": "2022-12-31",
        "max": 35,
    },
    {
        "cat": "timeline", "slug": "2024-rate-pivot",
        "title": "2024: разворот ставок и ралли",
        "type": "timeline",
        "tags": ["2024", "ставки", "ФРС", "ралли"],
        "kw": [
            "снижени ставк", "понижени ставк", "rate cut", "pivot",
            "разворот", "смягчени", "rally", "ралли",
            "мягкая посадк", "soft landing",
        ],
        "date_from": "2024-01-01",
        "date_to": "2024-12-31",
        "max": 30,
    },
    {
        "cat": "timeline", "slug": "2025-2026-ai-era",
        "title": "2025–2026: эра AI и Magnificent 7",
        "type": "timeline",
        "tags": ["2025", "2026", "AI", "Magnificent 7", "технологии"],
        "kw": [
            "искусственн интеллект", " ai ", "chatgpt", "openai",
            "nvidia", "mag", "magnificent", "полупроводник",
            "семёрк", "великолепн", "chip", "semiconductor",
        ],
        "date_from": "2025-01-01",
        "date_to": "2026-12-31",
        "max": 30,
    },
]

# ── Helpers ────────────────────────────────────────────────────────────

AUTOGEN_START = "<!-- autogen:quotes:start -->"
AUTOGEN_END = "<!-- autogen:quotes:end -->"


def match_score(text: str, kws: list[str]) -> int:
    lo = text.lower()
    return sum(1 for k in kws if k in lo)


def truncate(text: str, limit: int = 600) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(".,;: ") + " […]"


def format_quote(rec: dict) -> str:
    txt = truncate(rec.get("text") or "")
    lines = []
    for line in txt.split("\n"):
        lines.append(f"> {line}")
    link = f"[{rec['date']}]({rec['source']}#{rec['msg_id']})"
    lines.append(f">\n> — {link}")
    return "\n".join(lines)


def build_quotes_block(matches: list[dict], max_q: int) -> str:
    if not matches:
        return "_Нет подходящих сообщений._"
    # Sort by date
    matches.sort(key=lambda r: (r["date"], r["time"], r["id"]))
    # If too many, keep top-scored, then re-sort by date
    if len(matches) > max_q:
        # Keep first 5 + last 5 + top-scored middle
        first = matches[:5]
        last = matches[-5:]
        middle = sorted(matches[5:-5], key=lambda r: -r["_score"])
        middle = middle[: max_q - 10]
        combined_ids = {r["id"] for r in first + last + middle}
        matches = [r for r in matches if r["id"] in combined_ids]
        matches.sort(key=lambda r: (r["date"], r["time"], r["id"]))

    parts = []
    cur_year = None
    for r in matches:
        y = r["date"][:4]
        if y != cur_year:
            cur_year = y
            parts.append(f"\n### {y}\n")
        parts.append(format_quote(r))
        parts.append("")
    return "\n".join(parts)


def skeleton_page(spec: dict) -> str:
    """Create initial page skeleton with placeholders."""
    fm = textwrap.dedent(f"""\
    ---
    title: "{spec['title']}"
    type: {spec['type']}
    tags: {json.dumps(spec['tags'], ensure_ascii=False)}
    first_seen: ""
    last_seen: ""
    source_count: 0
    updated: {TODAY}
    ---
    """)
    body = textwrap.dedent(f"""\
    # {spec['title']}

    ## Краткое резюме

    _[синтез] TODO: написать резюме._

    ## Ключевые идеи

    - TODO

    ## Эволюция взглядов

    _Пока не выявлена._

    {AUTOGEN_START}
    _Цитаты ещё не сгенерированы._
    {AUTOGEN_END}

    ## См. также

    - TODO
    """)
    return fm + "\n" + body


def update_frontmatter(content: str, first: str, last: str, count: int) -> str:
    content = re.sub(
        r'first_seen:\s*"?[^"\n]*"?',
        f'first_seen: {first}',
        content,
    )
    content = re.sub(
        r'last_seen:\s*"?[^"\n]*"?',
        f'last_seen: {last}',
        content,
    )
    content = re.sub(
        r'source_count:\s*\d*',
        f'source_count: {count}',
        content,
    )
    content = re.sub(
        r'updated:\s*\S*',
        f'updated: {TODAY}',
        content,
    )
    return content


def process_page(spec: dict, corpus: list[dict], since: str | None) -> None:
    cat = spec["cat"]
    slug = spec["slug"]
    path = WIKI / cat / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)

    kws = spec["kw"]
    max_q = spec.get("max", 25)
    date_from = spec.get("date_from")
    date_to = spec.get("date_to")

    matches = []
    for r in corpus:
        text = (r.get("text") or "") + " " + (r.get("media") or "")
        # Date filter for timeline pages
        if date_from and r["date"] < date_from:
            continue
        if date_to and r["date"] > date_to:
            continue
        # RU filter (skip if >=2 hard RU terms)
        if ru_score(text) >= 2:
            continue
        sc = match_score(text, kws)
        if sc < 1:
            continue
        if since and r["date"] < since:
            continue
        r_copy = dict(r)
        r_copy["_score"] = sc
        matches.append(r_copy)

    quotes_block = build_quotes_block(matches, max_q)

    if path.exists():
        content = path.read_text(encoding="utf-8")
        # Replace autogen block
        if AUTOGEN_START in content and AUTOGEN_END in content:
            before = content[: content.index(AUTOGEN_START)]
            after = content[content.index(AUTOGEN_END) + len(AUTOGEN_END) :]
            new_block = f"{AUTOGEN_START}\n## Цитаты\n\n{quotes_block}\n{AUTOGEN_END}"
            content = before + new_block + after
        else:
            content += f"\n{AUTOGEN_START}\n## Цитаты\n\n{quotes_block}\n{AUTOGEN_END}\n"
    else:
        content = skeleton_page(spec)
        content = content.replace(
            f"{AUTOGEN_START}\n_Цитаты ещё не сгенерированы._\n{AUTOGEN_END}",
            f"{AUTOGEN_START}\n## Цитаты\n\n{quotes_block}\n{AUTOGEN_END}",
        )

    # Update frontmatter stats
    if matches:
        first = min(r["date"] for r in matches)
        last = max(r["date"] for r in matches)
        content = update_frontmatter(content, first, last, len(matches))

    path.write_text(content, encoding="utf-8")
    print(f"  {cat}/{slug}.md : {len(matches)} quotes")


# ── Main ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", help="Only include messages after YYYY-MM-DD")
    args = parser.parse_args()

    corpus = [
        json.loads(line)
        for line in CORPUS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    corpus.sort(key=lambda r: (r["date"], r["time"], r["id"]))
    print(f"corpus: {len(corpus)} messages")

    for spec in PAGE_SPECS:
        process_page(spec, corpus, args.since)

    print(f"\ndone: {len(PAGE_SPECS)} pages in wiki/")


if __name__ == "__main__":
    main()
