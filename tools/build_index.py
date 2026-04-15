#!/usr/bin/env python3
"""Build a thematic index (INDEX.md) from tools/chat.jsonl.

Approach: lightweight keyword-based tagging. Each theme has a list of Russian
and English keywords/regex fragments. Every message is scanned case-insensitively
and tagged with every theme whose keywords match. The index is then written as
a single Markdown file with:
  - Overview + per-year counts
  - Table of contents
  - One section per theme with chronological list of messages (date + headline +
    link back to the original Telegram HTML export).
Messages that do not match any theme land in a final "Прочее" bucket.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "tools" / "chat.jsonl"
OUT = ROOT / "INDEX.md"

# ---------------------------------------------------------------------------
# Thematic taxonomy.
# Order matters only for TOC display. A message can belong to several themes.
# Keywords are matched as substrings on a lower-cased version of the text.
# Use tuples of alternative spellings. Keep patterns reasonably specific to
# avoid false positives.
# ---------------------------------------------------------------------------

THEMES: list[tuple[str, str, list[str]]] = [
    (
        "philosophy",
        "Философия инвестирования и принципы",
        [
            "долгосроч", "дисциплин", "терпен", "принцип", "стратеги",
            "горизонт инвест", "сложный процент", "баффет", "богл",
            "пассивн", "инвестирование- это", "инвестирование это",
            "чудес не бывает", "не казино",
        ],
    ),
    (
        "behavior",
        "Поведенческие финансы и психология инвестора",
        [
            "поведенческ", "психолог", "когнитивн", "искажени", "эмоци",
            "страх", "жадност", "fomo", "паник", "иллюзи", "эффект ikea",
            "канеман", "ловушк", "bias",
        ],
    ),
    (
        "advisors",
        "Советники, управляющие, комиссии и продукты",
        [
            "советник", "консультант", "управляющ", "комисси", "впарив",
            "структурн", "страхов", "unit-linked", "unit linked", "иси",
            "пиф", "mutual fund", "продавец", "брокер",
        ],
    ),
    (
        "goals",
        "Финансовые цели, пенсия, FIRE, накопления",
        [
            "пенси", "финансов цел", "финансовой цел", "финансовые цел",
            "накоплен", "сбережени", "fire", "ранняя пенс", "подушк",
            "финансовая независ", "финансовой независ",
        ],
    ),
    (
        "portfolio",
        "Портфель: asset allocation, ребалансировка, диверсификация",
        [
            "портфел", "аллокаци", "allocation", "ребаланс", "диверсифик",
            "asset allocation", "распределени актив", "доля в портфел",
            "weights",
        ],
    ),
    (
        "risk",
        "Риск-менеджмент, волатильность, просадки",
        [
            "риск", "волатильн", "просадк", "drawdown", "stop", "хедж",
            "hedge", "var ", "sharpe", "шарп", "максимальная просадк",
        ],
    ),
    (
        "stocks_us",
        "Акции США и глобальные рынки",
        [
            "s&p", "s & p", "sp500", "s&p 500", "nasdaq", "dow ", "nyse",
            "сипи", "сипишк", "апл", "apple", "microsoft", "amazon",
            "tesla", "tsla", "nvidia", "meta ", "facebook", "google",
            "alphabet", "netflix", "fang", "faang", "mag 7", "mag7",
            "великолепн", "magnificent", "buyback", "байбэк",
        ],
    ),
    (
        "stocks_ru",
        "Акции РФ, Мосбиржа, российские эмитенты",
        [
            "мосбирж", "ртс", "imoex", "ммвб", "газпром", "сбер", "лукойл",
            "роснефт", "норникел", "яндекс", "новатэк", "магнит", "втб",
            "полюс", "алроса", "русал", "татнефт", "мтс ", "фосагр",
            "российск акц", "российские акц", "российского рынк",
            "российский рынок",
        ],
    ),
    (
        "bonds_ru",
        "Облигации рублёвые (ОФЗ, корпоративные)",
        [
            "офз", "облигац", "купон", "доходност облигац", "рцб", "ключев ставк",
            "ставк цб", "дюраци",
        ],
    ),
    (
        "bonds_fx",
        "Еврооблигации и валютные бонды",
        [
            "еврооблиг", "евробонд", "eurobond", "замещающ облиг",
            "валютн облиг", "treasury", "treasuries", "tips", "казначейск",
            "us10y", "us 10y", "us10", "us 2y", "us2y", "трежер",
        ],
    ),
    (
        "etf",
        "ETF, индексные и биржевые фонды",
        [
            " etf", "etf ", "etf.", "etf,", " бпиф", "бпиф ", " finex",
            "finex ", "vanguard", "ishares", "spdr", "qqq", "spy ",
            " vti", "vti ", " voo", "voo ",
        ],
    ),
    (
        "gold",
        "Золото и драгметаллы",
        [
            "золот", "gold", "драгметалл", "серебр", "silver", "платин",
            "gld ", " gld", "палладий",
        ],
    ),
    (
        "crypto",
        "Криптовалюты",
        [
            "биткоин", "биткойн", "bitcoin", "btc ", " btc", "эфириум",
            "ethereum", "eth ", " eth", "крипто", "блокчейн", "altcoin",
            "альткоин", "стейблкоин", "usdt", "usdc",
        ],
    ),
    (
        "fx_usd_rub",
        "Валюта: доллар, рубль, евро, курсы",
        [
            "рубл", "доллар", "usd/rub", "usdrub", "eur/rub", "курс рубл",
            "курс доллар", "девальвац", "валютн рынок", "dxy", "индекс доллар",
        ],
    ),
    (
        "macro_rates",
        "Макро: ставки, инфляция, ФРС, ЦБ",
        [
            "инфляц", "процентн ставк", "фрс", "fed ", " fed", "ecb",
            "ецб", "ключевая ставк", "ставка цб", "банка росс", "цб рф",
            "powell", "пауэлл", "таргет", "бреттон",
        ],
    ),
    (
        "macro_crisis",
        "Макро: кризисы, рецессии, обвалы",
        [
            "кризис", "рецесси", "recession", "обвал", "коррекци", "медвеж",
            "bear market", "bull market", "бычий рынок", "пандеми", "covid",
            "ковид", "2008", "доткомов", "dot-com", "великая депресси",
        ],
    ),
    (
        "oil_commodities",
        "Нефть и commodities",
        [
            "нефт", "brent", "wti", "опек", "opec", "газ ", " газ", "уголь",
            "коммодит", "commodity", "сырь", "медь", "copper", "пшениц",
        ],
    ),
    (
        "emerging",
        "Китай и развивающиеся рынки",
        [
            "китай", "китайск", "hong kong", "гонконг", "em ", " em ",
            "emerging", "развивающ рынк", "индия", "бразили", "турц",
            "юань", "yuan", "cny",
        ],
    ),
    (
        "dividends",
        "Дивиденды и дивидендные стратегии",
        [
            "дивиденд", "dividend", "dgi", "dividend aristocrat", "ex-date",
            "реинвестировани диви",
        ],
    ),
    (
        "ipo",
        "IPO, SPAC, новые размещения",
        [
            " ipo", "ipo ", "ipo.", "ipo,", " spac", "spac ", "размещен",
            "первичное размещ", "andквот",
        ],
    ),
    (
        "real_estate",
        "Недвижимость и REIT",
        [
            "недвижимост", "квартир", "ипотек", "reit", "рейт ", "арендн",
            "аренду", "real estate",
        ],
    ),
    (
        "taxes",
        "Налоги, ИИС, льготы",
        [
            "налог", "ндфл", "иис", "льгот", "ldv", "вычет", "резидент",
        ],
    ),
    (
        "books_edu",
        "Книги, цитаты и образование",
        [
            "книг", "почитать", "автор пиш", "цитат", "исследован",
            "рекоменду прочитать", "богл", "грэм", "bogle", "graham",
            "talib", "талеб",
        ],
    ),
    (
        "forecasts",
        "Прогнозы, итоги года, взгляд вперёд",
        [
            "прогноз", "итог год", "итоги год", "взгляд вперед",
            "взгляд на ", "наш взгляд", "базов сценари", "ожидан на ",
            "прогноз на ", "outlook",
        ],
    ),
    (
        "tech",
        "Технологии, AI, инновации",
        [
            "искусственн интеллект", " ai ", " ии ", "chatgpt", "openai",
            "машинн обучен", "робот", "ark invest", "disrupt", "иннова",
            "полупроводник", "semicon", "chip",
        ],
    ),
    (
        "geopolitics",
        "Геополитика, санкции",
        [
            "санкци", "геополит", "геополитическ", "война", "конфликт",
            "украин", "нато", "nato", "иран", "израил",
        ],
    ),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WORD_RE = re.compile(r"\s+")


def headline(text: str, limit: int = 110) -> str:
    """Return the first non-empty line/sentence, shortened to `limit` chars."""
    if not text:
        return ""
    # First paragraph
    first = text.strip().split("\n", 1)[0]
    # Split on sentence terminators, keep first
    parts = re.split(r"(?<=[.!?])\s+", first, maxsplit=1)
    hl = parts[0] if parts else first
    hl = WORD_RE.sub(" ", hl).strip()
    if len(hl) > limit:
        hl = hl[: limit - 1].rstrip() + "…"
    # Escape characters that would break a Markdown link label
    hl = hl.replace("[", "(").replace("]", ")")
    return hl


def tag_message(text: str) -> list[str]:
    lo = text.lower()
    tags: list[str] = []
    for key, _title, kws in THEMES:
        for kw in kws:
            if kw in lo:
                tags.append(key)
                break
    return tags


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    records = [json.loads(line) for line in CORPUS.read_text(encoding="utf-8").splitlines() if line.strip()]
    records.sort(key=lambda r: (r["date"], r["time"], r["id"]))

    by_theme: dict[str, list[dict]] = defaultdict(list)
    theme_for: dict[int, list[str]] = {}
    untagged: list[dict] = []

    for r in records:
        body = (r.get("text") or "") + " " + (r.get("media") or "")
        tags = tag_message(body)
        theme_for[r["id"]] = tags
        if tags:
            for t in tags:
                by_theme[t].append(r)
        else:
            untagged.append(r)

    # ---------- Write INDEX.md ----------
    lines: list[str] = []
    lines.append("# Тематический индекс канала «Капитал» (SGCapital)")
    lines.append("")
    lines.append(
        f"Источник: Telegram-экспорт (`messages.html`, `messages2.html`, `messages3.html`)."
    )
    lines.append(
        f"Всего сообщений: **{len(records)}**, период: **{records[0]['date']} — {records[-1]['date']}**."
    )
    lines.append("")
    lines.append("Индекс построен автоматически (`tools/build_index.py`) на основе"
                 " чистого JSONL-корпуса `tools/chat.jsonl`. Каждое сообщение тегируется"
                 " по списку ключевых слов, поэтому одно сообщение может попасть в"
                 " несколько тем. Ссылки ведут на нужное сообщение в исходных HTML"
                 " файлах экспорта — они работают, если открыть индекс рядом с"
                 " `messages*.html`.")
    lines.append("")

    # Year stats
    by_year = Counter(r["date"][:4] for r in records)
    lines.append("## Сообщений по годам")
    lines.append("")
    lines.append("| Год | Сообщений |")
    lines.append("|---:|---:|")
    for y in sorted(by_year):
        lines.append(f"| {y} | {by_year[y]} |")
    lines.append("")

    # TOC
    lines.append("## Содержание")
    lines.append("")
    total_tagged = 0
    for key, title, _ in THEMES:
        n = len(by_theme.get(key, []))
        total_tagged += n
        anchor = key
        lines.append(f"- [{title}](#{anchor}) — {n}")
    lines.append(f"- [Прочее / без явной темы](#other) — {len(untagged)}")
    lines.append("")
    covered = sum(1 for r in records if theme_for[r["id"]])
    lines.append(
        f"_Покрытие темами: {covered}/{len(records)} сообщений ({covered*100//len(records)}%)._"
    )
    lines.append("")

    # Per-theme sections
    def emit_section(anchor: str, title: str, items: list[dict]) -> None:
        lines.append(f'<a id="{anchor}"></a>')
        lines.append(f"## {title}")
        lines.append("")
        if not items:
            lines.append("_Нет сообщений._")
            lines.append("")
            return
        items = sorted(items, key=lambda r: (r["date"], r["time"], r["id"]))
        lines.append(f"_Всего: {len(items)}_")
        lines.append("")
        current_year = None
        for r in items:
            year = r["date"][:4]
            if year != current_year:
                current_year = year
                lines.append(f"### {year}")
                lines.append("")
            hl = headline(r.get("text") or r.get("media") or "")
            link = f"{r['source']}#{r['msg_id']}"
            lines.append(f"- **{r['date']}** — [{hl}]({link})")
        lines.append("")

    for key, title, _ in THEMES:
        emit_section(key, title, by_theme.get(key, []))
    emit_section("other", "Прочее / без явной темы", untagged)

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} with {len(records)} messages, "
          f"{len(THEMES)} themes, {covered} tagged")


if __name__ == "__main__":
    main()
