#!/usr/bin/env python3
"""Build the evidence sidecars and the catalog for `wiki/`.

What this does:

1. For each topic in WIKI_TOPICS — the evergreen-only subset of themes, with
   Russia-specific topics explicitly excluded (per CLAUDE.md §2.2) — match
   messages in `tools/chat.jsonl` by keyword and write a chronological list
   to `wiki/_sources/<topic>.md`. These files are the "Первоисточники"
   appendix that hand-written synthesis pages link to.

2. Scan `wiki/**/*.md` (skipping `_sources/` and `index.md` itself) and
   regenerate `wiki/index.md` — a catalog grouped by top-level directory,
   showing the first H1 as the title and the first non-empty line after it
   as the teaser.

What this does NOT do:

- It never touches hand-written pages (principles/, portfolio/, assets/,
  behavior/, macro/, overview.md, log.md).
- It never writes synthesis, prose, or interpretations. Only lists and
  catalog metadata.
- It never reaches outside the repository or the corpus file.

Usage:
    python3 tools/build_wiki.py
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "tools" / "chat.jsonl"
WIKI = ROOT / "wiki"
SOURCES = WIKI / "_sources"
INDEX = WIKI / "index.md"

# ---------------------------------------------------------------------------
# Evergreen taxonomy (subset of build_index.THEMES, RU-specific topics removed).
# Slug -> (human title, keyword list). Keywords match case-insensitively as
# substrings of the message text, same contract as build_index.py.
# ---------------------------------------------------------------------------

WIKI_TOPICS: list[tuple[str, str, list[str]]] = [
    (
        "passive-vs-active",
        "Пассивное vs активное инвестирование",
        [
            "пассивн", "индексн фонд", "индексных фонд", "индексные фонд",
            "активн управлен", "индексн инвест", "обыграть рынок",
            "обогнать рынок", "индексн стратеги",
        ],
    ),
    (
        "commissions",
        "Комиссии и издержки",
        [
            "комисси", "expense ratio", "вознагражд за управлен",
            "платa за управлен", "плату за управлен", "издержк",
            "базисных пункт", "базисные пункт",
        ],
    ),
    (
        "long-horizon",
        "Долгосрочный горизонт и сложный процент",
        [
            "долгосроч", "сложный процент", "горизонт инвест",
            "длинный горизонт", "терпен",
        ],
    ),
    (
        "risk-and-drawdowns",
        "Риск, волатильность, просадки",
        [
            "просадк", "drawdown", "волатильн", "риск", "шарп", "sharpe",
            "максимальн просадк",
        ],
    ),
    (
        "asset-allocation",
        "Asset allocation",
        [
            "аллокаци", "asset allocation", "распределен актив",
            "распределени актив", "доля в портфел", "веса в портфел",
        ],
    ),
    (
        "rebalancing",
        "Ребалансировка",
        [
            "ребаланс", "rebalanc",
        ],
    ),
    (
        "diversification",
        "Диверсификация",
        [
            "диверсифик", "корреляц", "корзин актив",
        ],
    ),
    (
        "equities-global",
        "Глобальные акции",
        [
            "s&p", "s & p", "sp500", "s&p 500", "nasdaq", "msci world",
            "msci acwi", "vti ", " vti", "voo ", " voo", "global equit",
            "широк рынок акций", "глобальн рынок акций", "мировой рынок акций",
        ],
    ),
    (
        "bonds-global",
        "Глобальные облигации",
        [
            "treasury", "treasuries", "tips ", " tips", "казначейск",
            "us10y", "us 10y", "us 2y", "us2y", "трежер", "agg ",
            "глобальн облигаци", "global bond",
        ],
    ),
    (
        "gold",
        "Золото",
        [
            "золот", "gold", "драгметалл", "gld ", " gld",
        ],
    ),
    (
        "crypto",
        "Криптовалюты",
        [
            "биткоин", "биткойн", "bitcoin", "btc ", " btc", "эфириум",
            "ethereum", "eth ", " eth", "крипто", "блокчейн",
        ],
    ),
    (
        "biases",
        "Поведенческие ловушки",
        [
            "поведенческ", "психолог инвестор", "когнитивн", "искажени",
            "эмоци", "страх", "жадност", "fomo", "паник", "иллюзи",
            "канеман", "bias",
        ],
    ),
    (
        "advisors-and-products",
        "Советники, управляющие, токсичные продукты",
        [
            "советник", "консультант", "управляющ", "впарив",
            "структурн продукт", "unit-linked", "unit linked", "пиф ",
            "mutual fund", "активн фонд",
        ],
    ),
    (
        "crises-and-recessions",
        "Кризисы и рецессии",
        [
            "кризис", "рецесси", "recession", "обвал", "медвеж рынок",
            "bear market", "пандеми", "covid", "2008", "доткомов",
            "великая депресси",
        ],
    ),
    (
        "inflation-and-rates",
        "Инфляция и ставки",
        [
            "инфляц", "процентн ставк", "фрс", " fed ", "ecb", "ецб",
            "таргет инфляц", "ключев ставк", "ставка цб",
        ],
    ),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WS = re.compile(r"\s+")


def headline(text: str, limit: int = 120) -> str:
    if not text:
        return ""
    first = text.strip().split("\n", 1)[0]
    parts = re.split(r"(?<=[.!?])\s+", first, maxsplit=1)
    hl = parts[0] if parts else first
    hl = WS.sub(" ", hl).strip()
    if len(hl) > limit:
        hl = hl[: limit - 1].rstrip() + "…"
    return hl.replace("[", "(").replace("]", ")")


def tag_matches(text: str, keywords: list[str]) -> bool:
    lo = text.lower()
    return any(kw in lo for kw in keywords)


# ---------------------------------------------------------------------------
# Evidence sidecars
# ---------------------------------------------------------------------------


def build_sources(records: list[dict]) -> None:
    SOURCES.mkdir(parents=True, exist_ok=True)
    for slug, title, keywords in WIKI_TOPICS:
        hits = [
            r
            for r in records
            if tag_matches((r.get("text") or "") + " " + (r.get("media") or ""), keywords)
        ]
        hits.sort(key=lambda r: (r["date"], r["time"], r["id"]))
        out = SOURCES / f"{slug}.md"
        lines: list[str] = []
        lines.append(f"# Первоисточники — {title}")
        lines.append("")
        lines.append(
            "_Автогенерировано `tools/build_wiki.py` из `tools/chat.jsonl`."
            " Не редактируйте вручную — изменения будут перезаписаны."
            " Для синтеза см. соответствующую страницу в `wiki/`._"
        )
        lines.append("")
        lines.append(f"**Совпадений:** {len(hits)}")
        lines.append("")
        if not hits:
            lines.append("_Сообщений по ключевым словам не найдено._")
        else:
            current_year = None
            for r in hits:
                year = r["date"][:4]
                if year != current_year:
                    current_year = year
                    lines.append(f"## {year}")
                    lines.append("")
                hl = headline(r.get("text") or r.get("media") or "")
                rel = f"../../{r['source']}#{r['msg_id']}"
                lines.append(f"- **{r['date']}** `chat:{r['msg_id']}` — [{hl}]({rel})")
            lines.append("")
        out.write_text("\n".join(lines), encoding="utf-8")
        print(f"  sources: {out.relative_to(ROOT)} ({len(hits)} hits)")


# ---------------------------------------------------------------------------
# Catalog (wiki/index.md)
# ---------------------------------------------------------------------------

SECTION_ORDER = [
    ("principles", "Принципы"),
    ("portfolio", "Портфель"),
    ("assets", "Классы активов"),
    ("behavior", "Поведение"),
    ("macro", "Макро"),
]

SKIP_PATHS = {"index.md", "_sources"}


def extract_meta(path: Path) -> tuple[str, str]:
    """Return (title, teaser) for a wiki page."""
    text = path.read_text(encoding="utf-8").strip().splitlines()
    title = path.stem
    teaser = ""
    for i, line in enumerate(text):
        line = line.strip()
        if line.startswith("# "):
            title = line[2:].strip()
            # Find first non-empty, non-heading line after H1.
            for follow in text[i + 1 :]:
                s = follow.strip()
                if not s or s.startswith("#"):
                    continue
                # Strip markdown emphasis and blockquote markers.
                s = re.sub(r"^>\s*", "", s)
                s = re.sub(r"[*_`]", "", s)
                teaser = s[:160] + ("…" if len(s) > 160 else "")
                break
            break
    return title, teaser


def build_index() -> None:
    sections: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    top_pages: list[tuple[str, str, str]] = []  # (rel_path, title, teaser)

    for md in sorted(WIKI.rglob("*.md")):
        rel = md.relative_to(WIKI).as_posix()
        if rel == "index.md" or rel.startswith("_sources/"):
            continue
        title, teaser = extract_meta(md)
        parts = rel.split("/", 1)
        if len(parts) == 1:
            top_pages.append((rel, title, teaser))
        else:
            sections[parts[0]].append((rel, title, teaser))

    lines: list[str] = []
    lines.append("# Каталог wiki")
    lines.append("")
    lines.append(
        "_Автогенерировано `tools/build_wiki.py`. Не редактируйте вручную._"
    )
    lines.append("")

    # Top-level pages first (overview, log, ...).
    if top_pages:
        lines.append("## Общее")
        lines.append("")
        for rel, title, teaser in sorted(top_pages):
            if teaser:
                lines.append(f"- [{title}]({rel}) — {teaser}")
            else:
                lines.append(f"- [{title}]({rel})")
        lines.append("")

    # Then sections in the declared order, then any leftover.
    seen_sections: set[str] = set()
    for slug, human in SECTION_ORDER:
        items = sorted(sections.get(slug, []))
        if not items:
            continue
        seen_sections.add(slug)
        lines.append(f"## {human}")
        lines.append("")
        for rel, title, teaser in items:
            if teaser:
                lines.append(f"- [{title}]({rel}) — {teaser}")
            else:
                lines.append(f"- [{title}]({rel})")
        lines.append("")

    for slug in sorted(set(sections) - seen_sections):
        items = sorted(sections[slug])
        lines.append(f"## {slug}")
        lines.append("")
        for rel, title, teaser in items:
            if teaser:
                lines.append(f"- [{title}]({rel}) — {teaser}")
            else:
                lines.append(f"- [{title}]({rel})")
        lines.append("")

    # Footer: list of evidence sidecars.
    src_files = sorted(SOURCES.glob("*.md")) if SOURCES.exists() else []
    if src_files:
        lines.append("## Первоисточники (автогенерированные)")
        lines.append("")
        for f in src_files:
            rel = f.relative_to(WIKI).as_posix()
            title, _ = extract_meta(f)
            lines.append(f"- [{title}]({rel})")
        lines.append("")

    INDEX.write_text("\n".join(lines), encoding="utf-8")
    print(f"  catalog: {INDEX.relative_to(ROOT)} ({len(top_pages)} top + "
          f"{sum(len(v) for v in sections.values())} sectioned)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    records = [
        json.loads(line)
        for line in CORPUS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    records.sort(key=lambda r: (r["date"], r["time"], r["id"]))
    print(f"loaded {len(records)} messages from {CORPUS.relative_to(ROOT)}")

    WIKI.mkdir(parents=True, exist_ok=True)
    build_sources(records)
    build_index()


if __name__ == "__main__":
    main()
