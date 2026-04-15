#!/usr/bin/env python3
"""Generate a PDF of the €300k allocation table.

Output: examples/portfolio-300k-eur.pdf

Version 4 — Spanish tax residency (Comunidad Valenciana), EUR unit of
account, 10-year horizon, quarterly €25k contributions, crypto allowed.
All instruments are UCITS (Ireland-domiciled) Acc share classes
tradeable on EU exchanges so the portfolio is legally accessible to a
Spanish retail investor and avoids the PRIIPs wall on US-domiciled ETFs.
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
    ("Глобальные акции", None,          "52%", "€156 000",
     "10y горизонт → каноническая equity-база"),
    ("",                 "CSPX — S&P 500 UCITS Acc (IE00B5BMR087)",          "20%", "€60 000",
     "chat:message2489 — США в недовесе vs кап-вес"),
    ("",                 "EXUS — MSCI World ex-US UCITS Acc (IE00BKBF6H24)", "18%", "€54 000",
     "chat:message2405 — разворот Европы"),
    ("",                 "EMIM — MSCI EM IMI UCITS Acc (IE00BKM4GZ66)",      "8%",  "€24 000",
     "chat:message2489 — VEU/SPY пробой"),
    ("",                 "IWMO — MSCI World Momentum UCITS Acc (IE00BP3QZ825)", "6%",  "€18 000",
     "chat:message97 — факторный оверлей"),

    ("Облигации (EUR)",  None,          "18%", "€54 000",
     "Валютный матчинг к расходам + короткая дюрация"),
    ("",                 "VAGF — Global Agg Bond EUR Hedged Acc (IE00BG47KH54)", "10%", "€30 000",
     "chat:message2414 — без длинных Трежерис"),
    ("",                 "IBGS — € Govt Bond 1-3yr Acc (IE00B3VTMJ91)",      "8%", "€24 000",
     "EUR «подушка» для квартальных ребалансов"),

    ("Драгметаллы",      None,          "17%", "€51 000",
     "Структурная защитная корзина"),
    ("",                 "SGLN — iShares Physical Gold ETC (IE00B4ND3602)",  "9%",  "€27 000",
     "chat:message56, chat:message2229"),
    ("",                 "SSLN — iShares Physical Silver ETC (IE00B4NCWG09)", "3%",  "€9 000",
     "Опережает золото на поздней фазе"),
    ("",                 "GDGB — VanEck Gold Miners UCITS (IE00BQQP9F84)",   "2%",  "€6 000",
     "«Рычаг» к золоту"),
    ("",                 "PHPD — WisdomTree Palladium ETC (JE00B1VS3002)",   "2%",  "€6 000",
     "chat:message2453 — просыпается последним"),
    ("",                 "PHPT — WisdomTree Platinum ETC (JE00B1VS2W53)",    "1%",  "€3 000",
     "chat:message56 — иная фундаменталка"),

    ("Промсырьё / энергия", None,       "5%",  "€15 000",
     "Инфляционный хедж помимо драгов"),
    ("",                 "COPG — Global X Copper Miners UCITS",              "3%",  "€9 000",
     "chat:message2414 — медь пробивает сопротивление"),
    ("",                 "IUES — S&P 500 Energy Sector UCITS (IE00B42NKQ00)", "2%",  "€6 000",
     "chat:message2414 — «нефть я бы не хоронил»"),

    ("Крипта",           None,          "5%",  "€15 000",
     "Структурный тезис + инфляционный бенефициар"),
    ("",                 "BTCE — 21Shares Bitcoin Core ETP (XETRA)",         "5%",  "€15 000",
     "chat:message2227, chat:message2414"),

    ("EUR кэш / MM",     None,          "3%",  "€9 000",
     "Минимальный буфер, ликвидность даёт бонд-часть"),
    ("",                 "XEON — EUR Overnight Rate Swap UCITS (LU0290358497)", "3%",  "€9 000",
     "≈ ставка ЕЦБ, T+0"),
]

TOTAL_ROW = ("ИТОГО", "", "100%", "€300 000", "")


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
    header = ["Блок / инструмент", "%", "EUR", "Источник"]
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
        "Модельный портфель на €300 000 · Испания / 10 лет", title_style))
    story.append(Paragraph(
        "Синтез по философии канала «Капитал» (SGCapital). Старт €300 000, "
        "квартальные пополнения €25 000 (40 взносов = +€1 000 000, нетто-взносы "
        "за 10 лет = €1 300 000; реалистичный финал с ростом ≈ €1.7–1.9 млн). "
        "Юрисдикция — Comunidad Valenciana, валюта учёта и расходов — EUR. "
        "Все инструменты — UCITS Acc, торгуемые на EU-биржах.",
        subtitle_style))

    story.append(Paragraph("Итоговая аллокация", h2_style))
    story.append(build_table())

    story.append(Paragraph("Ключевые решения", h2_style))
    bullets = [
        "<b>Equities 52%, внутри США ≈ 20%.</b> 10y — каноническая "
        "дальнодистанционная база канала (chat:message42, chat:message1310). "
        "США держим в недовесе vs кап-веса (~60%) на основе chat:message2489 "
        "(январь 2026) — аллокация иностранцев в США у исторических максимумов.",
        "<b>Облигации 18%, всё в EUR.</b> VAGF (global aggregate EUR hedged) + "
        "IBGS (€ govt 1-3yr). Длинных Трежерис нет (chat:message2414, июнь 2025). "
        "Короче, чем в 5y-версии: при 10y горизонте генератор доходности — "
        "акции, бонды нужны только как буфер волатильности.",
        "<b>Драгметаллы 17%.</b> Структурный цикл из chat:message2229 (янв 2024) "
        "в 2025 дал +170% по золотодобытчикам и +38% по PALL; на 10y выходить "
        "из блока преждевременно. Пересмотр — при развороте цикла ставок ФРС в "
        "обратную сторону.",
        "<b>Крипта 5% через BTCE (21Shares, XETRA).</b> Спотовые BTC-ETF в "
        "US-форме физлицу в ES недоступны. BTCE — UCITS-ETP на физический BTC, "
        "торгуется в EUR на Deutsche Börse; учёт через Modelo 720, не 721. "
        "На 10y окне волатильность BTC смягчается, поэтому доля чуть выше 5y-версии.",
        "<b>Cash 3% — минимум.</b> Квартальные взносы €25 000 обеспечивают "
        "всю необходимую ликвидность на ребаланс; держать больше — значит "
        "терять доходность без причины.",
        "<b>Ребалансировка через пополнения, а не продажи.</b> Каждый квартал "
        "€25 000 направляются в наиболее просевший vs целевой вес блок. "
        "На 10y (40 кварталов) это мощнейший DCA-механизм: база не трогается, "
        "CGT (19–28%) не платится.",
        "<b>Жёсткая ребалансировка (с продажами) — раз в год либо при "
        "отклонении ≥5 п.п.</b> Правило из chat:message559. Только если "
        "квартальных взносов не хватило выровнять дрифт.",
    ]
    for b in bullets:
        story.append(Paragraph("• " + b, body_style))

    story.append(Paragraph("Под Испанию: налоговая гигиена", h2_style))
    tax = [
        "<b>Все ETF — Acc (накопление).</b> Дивиденды реинвестируются внутри "
        "фонда → нет ежегодного taxable event по дивидендам, налог платится "
        "только при продаже.",
        "<b>Modelo 720 (иностранные счета/активы) + Modelo 721 (крипта).</b> "
        "Порог €50 000 по каждой категории. С €300k старта порог перейдётся "
        "сразу по 720. BTCE выбран как securitized ETP на брокерском счёте, "
        "поэтому он идёт в 720, а не в 721 — учёт проще.",
        "<b>CGT-лестница 2026 (ES):</b> 19% до €6k, 21% €6–50k, 23% €50–200k, "
        "27% €200–300k, 28% свыше €300k. Главная причина "
        "ребалансировать докупками, а не продажами.",
        "<b>Impuesto sobre el Patrimonio — подробнее ниже.</b> Федеральный "
        "mínimo exento €700k + €300k на vivienda habitual. На старте (€300k) "
        "не задевает; к 4–5 году нетто-взносы приблизятся к порогу, начнёт "
        "иметь значение выбор CCAA.",
        "<b>ITSGF (federal).</b> Impuesto Temporal de Solidaridad de las "
        "Grandes Fortunas действует там, где CCAA обнулила Patrimonio через "
        "bonificación, но только при состоянии свыше €3 млн. На горизонте "
        "этого портфеля не актуально.",
    ]
    for b in tax:
        story.append(Paragraph("• " + b, body_style))

    story.append(Paragraph(
        "Comunidad Valenciana: Patrimonio конкретно", h2_style))
    story.append(Paragraph(
        "<b>Comunidad Valenciana.</b> С 2023 г. exento снижен с €600k "
        "до €500k, bonificación нет, шкала — государственная (0.2–3.5%). "
        "ITSGF в CCAA, которые Patrimonio взимают (как Валенсия), "
        "зачитывается против него — двойного удара нет. "
        "Дополнительный exento €300k на vivienda habitual применяется "
        "сверху, если оформляется основное жильё в собственности.",
        body_style))

    story.append(Paragraph(
        "Patrimonio год-за-годом (Валенсия, 10 лет)", h2_style))
    proj_data = [
        ["Год", "База*",    "Свыше €500k", "Patrimonio/год**",
            "Patrimonio (с VH)***"],
        ["0",   "€300k",    "—",        "€0",       "€0"],
        ["1",   "€415k",    "—",        "€0",       "€0"],
        ["2",   "€536k",    "€36k",     "≈ €70",    "€0"],
        ["3",   "€663k",    "€163k",    "≈ €330",   "€0"],
        ["4",   "€796k",    "€296k",    "≈ €720",   "€0"],
        ["5",   "€936k",    "€436k",    "≈ €1 350", "≈ €270"],
        ["6",   "€1 083k",  "€583k",    "≈ €2 080", "≈ €800"],
        ["7",   "€1 237k",  "€737k",    "≈ €2 920", "≈ €1 400"],
        ["8",   "€1 399k",  "€899k",    "≈ €3 890", "≈ €2 090"],
        ["9",   "€1 569k",  "€1 069k",  "≈ €5 010", "≈ €2 890"],
        ["10",  "€1 747k",  "€1 247k",  "≈ €7 200", "≈ €3 810"],
    ]
    proj_widths = [12 * mm, 28 * mm, 28 * mm, 35 * mm, 37 * mm]
    proj_tbl = Table(proj_data, colWidths=proj_widths, repeatRows=1)
    proj_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b2545")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME",   (0, 0), (-1, 0), FONT_BOLD),
        ("FONTSIZE",   (0, 0), (-1, 0), 8),
        ("FONTNAME",   (0, 1), (-1, -1), FONT_REGULAR),
        ("FONTSIZE",   (0, 1), (-1, -1), 8),
        ("ALIGN",      (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",       (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
            [colors.whitesmoke, colors.white]),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("TOPPADDING",    (0, 0), (-1, 0), 5),
    ]))
    story.append(proj_tbl)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<i>* База = портфель на конец года, сценарий +5% годовых на "
        "существующую базу + €100k взносы/год. "
        "** Государственная прогрессивная шкала Patrimonio на базу свыше "
        "€500k (0.2% / 0.3% / 0.5% / 0.9% …). "
        "*** С учётом доп. exento €300k за vivienda habitual (итого €800k). "
        "Это главный единичный рычаг на 10y горизонте.</i>",
        body_style))
    story.append(Paragraph(
        "<b>Суммарно за 10 лет:</b> без vivienda ≈ €23 500 Patrimonio; "
        "с vivienda ≈ €11 300. Разница ≈ €12 000 — это 0.7% от итогового "
        "портфеля. "
        "<b>Цена переезда в Мадрид/Андалусию</b> (bonificación 100%, "
        "ITSGF не кусает до €3 млн): ≈ €23 500 за 10 лет = €2 350/год "
        "экономии в среднем.",
        body_style))

    story.append(Paragraph(
        "Что это значит для стратегии на 10 лет:", body_style))
    val_actions = [
        "<b>Vivienda habitual — MUST, если ещё не оформлена.</b> "
        "Дополнительный exento €300k срезает кумулятивный Patrimonio "
        "почти вдвое (≈ €12 000 сэкономленных за 10 лет).",
        "<b>Plan de Pensiones (€1 500/год базовый лимит для физлиц).</b> "
        "На 10 лет это €15k отчислений, уменьшающих И IRPF base, "
        "И Patrimonio base. Скромная, но гарантированная экономия.",
        "<b>Переезд в Мадрид/Андалусию/Галисию</b> — к 6–7 году начинает "
        "окупаться (>€2 000/год). Решение не налоговое, но если есть "
        "гибкость — учитывать.",
        "<b>SICAV/ETF-обёртка life-insurance</b> — для поздних лет "
        "(после года 7, когда Patrimonio бьёт €3k+/год). Unit-linked "
        "испанской страховой с UCITS-корзиной может откладывать "
        "Patrimonio-начисление. Это overengineering, оценивать лично с gestor'ом.",
        "<b>Контроль весов через DCA.</b> На 10y окне важнее всего "
        "не трогать базу продажами. Квартальных €25k достаточно для "
        "всех штатных ребалансов; жёсткий sell только при жёстком "
        "дрифте ≥7 п.п.",
    ]
    for b in val_actions:
        story.append(Paragraph("• " + b, body_style))

    story.append(Paragraph("Логика квартальных взносов €25 000", h2_style))
    dca = [
        "Каждый квартал: посмотреть текущие веса блоков vs целевые в таблице выше.",
        "Весь €25 000 распределить в блоки, которые <b>ниже</b> цели, "
        "пропорционально размеру «дыры». Не продавать ничего.",
        "Если все блоки в пределах ±2 п.п. от цели — распределить взнос по "
        "целевым весам (52% в акции, 18% в бонды, 17% в драгметаллы, "
        "5% в commodities, 5% в крипту, 3% в кэш).",
        "Один раз в год (например, в январе, до декларации Modelo 720) — "
        "зафиксировать snapshot весов и свериться с правилом «5 п.п.» для "
        "ручного ребаланса.",
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
    out = Path(__file__).parent / "portfolio-300k-eur.pdf"
    build_pdf(out)
    print(f"wrote {out}")
