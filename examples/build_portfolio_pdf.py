#!/usr/bin/env python3
"""Generate a one-page PDF of the $300k allocation table.

Output: examples/portfolio-300k-usd.pdf

Version 2 — Spanish tax residency, EUR expense currency, 5-year horizon,
quarterly $25k contributions, crypto allowed. All instruments are UCITS
(Ireland-domiciled) Acc share classes tradeable on EU exchanges so the
portfolio is legally accessible to a Spanish retail investor and avoids
the PRIIPs wall on US-domiciled ETFs.
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)


# --- fonts -------------------------------------------------------------------
FONT_CANDIDATES = [
    ("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ("DejaVuSans-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
for name, path in FONT_CANDIDATES:
    if Path(path).exists():
        try:
            pdfmetrics.registerFont(TTFont(name, path))
            if name == "DejaVuSans":
                FONT_REGULAR = "DejaVuSans"
            elif name == "DejaVuSans-Bold":
                FONT_BOLD = "DejaVuSans-Bold"
        except Exception:
            pass


# --- allocation data ---------------------------------------------------------
# (block, instrument, pct, usd, rationale)
# Totals per block row have instrument=None.
# All instruments are UCITS Acc on EU exchanges (Spanish retail accessible).
ROWS = [
    ("Глобальные акции", None,          "45%", "$135 000",
     "5y горизонт → скромнее 50%"),
    ("",                 "CSPX — S&P 500 UCITS Acc (IE00B5BMR087)",          "17%", "$51 000",
     "chat:message2489 — США в недовесе"),
    ("",                 "EXUS — MSCI World ex-US UCITS Acc (IE00BKBF6H24)", "17%", "$51 000",
     "chat:message2405 — разворот Европы"),
    ("",                 "EMIM — MSCI EM IMI UCITS Acc (IE00BKM4GZ66)",      "7%",  "$21 000",
     "chat:message2489 — VEU/SPY пробой"),
    ("",                 "IWMO — MSCI World Momentum UCITS Acc (IE00BP3QZ825)", "4%",  "$12 000",
     "chat:message97 — факторный оверлей"),

    ("Облигации (EUR)",  None,          "22%", "$66 000",
     "Валютный матчинг к расходам + короткая дюрация"),
    ("",                 "VAGF — Global Agg Bond EUR Hedged Acc (IE00BG47KH54)", "12%", "$36 000",
     "chat:message2414 — без длинных Трежерис"),
    ("",                 "IBGS — € Govt Bond 1-3yr Acc (IE00B3VTMJ91)",      "10%", "$30 000",
     "EUR «подушка» для квартальных ребалансов"),

    ("Драгметаллы",      None,          "16%", "$48 000",
     "Структурная защитная корзина"),
    ("",                 "SGLN — iShares Physical Gold ETC (IE00B4ND3602)",  "8%",  "$24 000",
     "chat:message56, chat:message2229"),
    ("",                 "SSLN — iShares Physical Silver ETC (IE00B4NCWG09)", "3%",  "$9 000",
     "Опережает золото на поздней фазе"),
    ("",                 "GDGB — VanEck Gold Miners UCITS (IE00BQQP9F84)",   "2%",  "$6 000",
     "«Рычаг» к золоту"),
    ("",                 "PHPD — WisdomTree Palladium ETC (JE00B1VS3002)",   "2%",  "$6 000",
     "chat:message2453 — просыпается последним"),
    ("",                 "PHPT — WisdomTree Platinum ETC (JE00B1VS2W53)",    "1%",  "$3 000",
     "chat:message56 — иная фундаменталка"),

    ("Промсырьё / энергия", None,       "5%",  "$15 000",
     "Инфляционный хедж помимо драгов"),
    ("",                 "COPG — Global X Copper Miners UCITS",              "3%",  "$9 000",
     "chat:message2414 — медь пробивает сопротивление"),
    ("",                 "IUES — S&P 500 Energy Sector UCITS (IE00B42NKQ00)", "2%",  "$6 000",
     "chat:message2414 — «нефть я бы не хоронил»"),

    ("Крипта",           None,          "4%",  "$12 000",
     "Структурный тезис + инфляционный бенефициар"),
    ("",                 "BTCE — 21Shares Bitcoin Core ETP (XETRA)",         "4%",  "$12 000",
     "chat:message2227, chat:message2414"),

    ("EUR кэш / MM",     None,          "8%",  "$24 000",
     "Пыль для ребалансировок + буфер на квартальные взносы"),
    ("",                 "XEON — EUR Overnight Rate Swap UCITS (LU0290358497)", "8%",  "$24 000",
     "≈ ставка ЕЦБ, T+0"),
]

TOTAL_ROW = ("ИТОГО", "", "100%", "$300 000", "")


# --- styles -----------------------------------------------------------------
styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "title",
    parent=styles["Title"],
    fontName=FONT_BOLD,
    fontSize=18,
    leading=22,
    spaceAfter=4,
    textColor=colors.HexColor("#0b2545"),
)
subtitle_style = ParagraphStyle(
    "subtitle",
    parent=styles["Normal"],
    fontName=FONT_REGULAR,
    fontSize=10,
    leading=13,
    textColor=colors.HexColor("#555555"),
    spaceAfter=10,
)
body_style = ParagraphStyle(
    "body",
    parent=styles["Normal"],
    fontName=FONT_REGULAR,
    fontSize=9,
    leading=12,
    spaceAfter=6,
)
h2_style = ParagraphStyle(
    "h2",
    parent=styles["Heading2"],
    fontName=FONT_BOLD,
    fontSize=12,
    leading=15,
    spaceBefore=10,
    spaceAfter=4,
    textColor=colors.HexColor("#0b2545"),
)
disclaimer_style = ParagraphStyle(
    "disclaimer",
    parent=styles["Normal"],
    fontName=FONT_REGULAR,
    fontSize=8,
    leading=11,
    textColor=colors.HexColor("#777777"),
    spaceBefore=10,
)


# --- table build -------------------------------------------------------------
def build_table():
    header = ["Блок / инструмент", "%", "USD", "Источник"]
    data = [header]

    block_row_indices = []  # rows that are "block summary" → bold + background
    for block, instrument, pct, usd, note in ROWS:
        if instrument is None:
            data.append([block, pct, usd, note])
            block_row_indices.append(len(data) - 1)
        else:
            data.append([f"    {instrument}", pct, usd, note])

    data.append([TOTAL_ROW[0], TOTAL_ROW[2], TOTAL_ROW[3], TOTAL_ROW[4]])
    total_row = len(data) - 1

    # Convert cells to Paragraph for wrapping on the "Источник" column.
    note_style = ParagraphStyle(
        "note", parent=body_style, fontSize=8, leading=10)
    for r in range(1, len(data)):
        cell = data[r][3]
        if cell:
            data[r][3] = Paragraph(cell, note_style)

    col_widths = [92 * mm, 13 * mm, 20 * mm, 55 * mm]
    t = Table(data, colWidths=col_widths, repeatRows=1)

    style = TableStyle([
        # header
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b2545")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME",   (0, 0), (-1, 0), FONT_BOLD),
        ("FONTSIZE",   (0, 0), (-1, 0), 9),
        ("ALIGN",      (1, 0), (2, 0), "RIGHT"),
        ("ALIGN",      (0, 0), (0, 0), "LEFT"),
        ("ALIGN",      (3, 0), (3, 0), "LEFT"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING",    (0, 0), (-1, 0), 6),

        # body defaults
        ("FONTNAME",   (0, 1), (-1, -1), FONT_REGULAR),
        ("FONTSIZE",   (0, 1), (-1, -1), 8),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",      (1, 1), (2, -1), "RIGHT"),
        ("GRID",       (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2),
            [colors.whitesmoke, colors.white]),

        # total row
        ("BACKGROUND", (0, total_row), (-1, total_row),
            colors.HexColor("#e8edf5")),
        ("FONTNAME",   (0, total_row), (-1, total_row), FONT_BOLD),
        ("FONTSIZE",   (0, total_row), (-1, total_row), 10),
    ])

    # block summary rows — bold + accent background
    for idx in block_row_indices:
        style.add("BACKGROUND", (0, idx), (-1, idx),
                  colors.HexColor("#dde6f2"))
        style.add("FONTNAME", (0, idx), (-1, idx), FONT_BOLD)
        style.add("FONTSIZE", (0, idx), (-1, idx), 9)

    t.setStyle(style)
    return t


# --- document ----------------------------------------------------------------
def build_pdf(output: Path):
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title="Portfolio $300k — SGCapital philosophy",
        author="Fin_Capital_2026 / wiki",
    )

    story = []

    story.append(Paragraph(
        "Модельный портфель на $300 000 · Испания / EUR / 5 лет", title_style))
    story.append(Paragraph(
        "Синтез по философии канала «Капитал» (SGCapital). Старт $300k, "
        "квартальные пополнения $25k (20 взносов = +$500k). "
        "Юрисдикция ES, валюта расходов EUR. Все инструменты — UCITS Acc на EU-биржах.",
        subtitle_style))

    story.append(Paragraph("Итоговая аллокация", h2_style))
    story.append(build_table())

    story.append(Paragraph("Ключевые решения", h2_style))
    bullets = [
        "<b>Equities 45% (меньше обычного), внутри США ≈ 17%.</b> "
        "Горизонт 5 лет короче канонических 10+, плюс аллокация иностранцев в "
        "акции США у исторических максимумов (chat:message2489, январь 2026) — "
        "снижаем концентрационный риск.",
        "<b>Облигации 22%, всё в EUR.</b> VAGF (global aggregate EUR hedged) + "
        "IBGS (€ govt 1-3yr). Длинных Трежерис нет (chat:message2414, июнь 2025). "
        "Валютный матчинг к расходам убирает FX-риск при выводе в EUR.",
        "<b>Драгметаллы 16% — осознанно много для 5y.</b> Структурный цикл из "
        "chat:message2229 (янв 2024) в 2025 дал +170% по золотодобытчикам и +38% по "
        "PALL; выходить пока рано, но блок чуть ужат против 10y-версии.",
        "<b>Крипта 4% через BTCE (21Shares, XETRA).</b> Спотовые BTC-ETF в "
        "US-форме (IBIT) физлицу в ES недоступны. BTCE — UCITS-ETP на физический BTC, "
        "торгуется в EUR/USD на Deutsche Börse.",
        "<b>Ребалансировка через пополнения, а не продажи.</b> Каждый квартал "
        "$25k направляются в наиболее просевший vs целевой вес блок. "
        "Это главный налоговый лайфхак для ES: продажи = CGT 19–28%, "
        "докупки — нет. За 5 лет (20 кварталов) базу можно не тревожить.",
        "<b>Жёсткая ребалансировка (с продажами) — раз в год либо при "
        "отклонении ≥5 п.п.</b> Правило из chat:message559. Но только если "
        "квартальных взносов не хватило выровнять дрифт.",
    ]
    for b in bullets:
        story.append(Paragraph("• " + b, body_style))

    story.append(Paragraph("Под Испанию: налоговая гигиена", h2_style))
    tax = [
        "<b>Все ETF — Acc (накопление).</b> Дивиденды реинвестируются внутри "
        "фонда → нет ежегодного taxable event по дивидендам, налог платится "
        "только при продаже.",
        "<b>Модело 720 / 721.</b> Если суммарная стоимость иностранных счетов "
        "и криптоактивов превысит €50 000 по категориям — обязательная "
        "декларация. С $300k старта порог перейдётся сразу, учесть при старте.",
        "<b>Impuesto sobre el Patrimonio.</b> Region-specific; в "
        "Мадриде/Андалусии эффективно 0% через bonificación, в Каталонии "
        "и Балеарах есть; плюс федеральный ITSGF на крупные состояния.",
        "<b>CGT-лестница 2026 (ES):</b> 19% до €6k, 21% €6–50k, 23% €50–200k, "
        "27% €200–300k, 28% свыше €300k. Это вторая причина избегать продаж.",
        "<b>BTC/крипта.</b> Выбран BTCE (securitized ETP), а не прямая "
        "покупка BTC на бирже — так экспозиция сидит на брокерском счёте и "
        "отчитывается через 720, а не через 721. Проще учёт.",
    ]
    for b in tax:
        story.append(Paragraph("• " + b, body_style))

    story.append(Paragraph("Логика квартальных взносов $25 000", h2_style))
    dca = [
        "Каждый квартал: посмотреть текущие веса блоков vs целевые в таблице выше.",
        "Весь $25k распределить в блоки, которые <b>ниже</b> цели, пропорционально "
        "размеру «дыры». Не продавать ничего.",
        "Если все блоки в пределах ±2 п.п. от цели — распределить взнос по "
        "целевым весам (фактически: 45% в акции, 22% в бонды и т.д.).",
        "Один раз в год (например, в январе, до декларации) — зафиксировать "
        "snapshot весов и свериться с правилом «5 п.п.» для ручного ребаланса.",
    ]
    for b in dca:
        story.append(Paragraph("• " + b, body_style))

    story.append(Paragraph("Чего в портфеле НЕТ и почему", h2_style))
    not_in = [
        "<b>US-domiciled ETF</b> (VTI, GLD, SLV, IBIT, BSV, SGOV...) — "
        "PRIIPs не пускает retail в ES + 15% US WHT.",
        "<b>Длинных Трежерис</b> (TLT/EDV/ZROZ) — chat:message2414.",
        "<b>Хедж-фондов, структурных нот, ДУ с комиссией ≥1%</b> — "
        "chat:message5, chat:message121, chat:message131.",
        "<b>Отдельных акций-хайпов</b> — chat:message154.",
        "<b>Шортов/инверсных ETF</b> — не играем против тренда "
        "(chat:message2329, chat:message2467).",
        "<b>RU-активов</b> — CLAUDE.md §2.2.",
    ]
    for b in not_in:
        story.append(Paragraph("• " + b, body_style))

    story.append(Paragraph(
        "<b>Дисклеймер.</b> Это не инвестиционная и не налоговая рекомендация. "
        "Документ — синтез явных высказываний канала «Капитал» (ссылки "
        "chat:messageNNN указывают на конкретные сообщения в tools/chat.jsonl) "
        "плюс технические ограничения испанского розничного инвестора. "
        "По Modelo 720/721 и Impuesto sobre el Patrimonio ОБЯЗАТЕЛЬНО "
        "проверить с локальным gestor'ом — правила ежегодно меняются. "
        "Сам канал в chat:message860 подчёркивает: «аллокация активов для "
        "каждого инвестора — дело очень индивидуальное». Решение — ваше.",
        disclaimer_style))

    doc.build(story)


if __name__ == "__main__":
    out = Path(__file__).parent / "portfolio-300k-usd.pdf"
    build_pdf(out)
    print(f"wrote {out}")
