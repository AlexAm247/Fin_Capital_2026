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
    ("Глобальные акции", None,          "62%", "€186 000",
     "10y + €800k в банке = портфель — чистый growth"),
    ("",                 "CSPX — S&P 500 UCITS Acc (IE00B5BMR087)",          "23%", "€69 000",
     "chat:message2489 — США в недовесе vs кап-вес"),
    ("",                 "EXUS — MSCI World ex-US UCITS Acc (IE00BKBF6H24)", "21%", "€63 000",
     "chat:message2405 — разворот Европы"),
    ("",                 "EMIM — MSCI EM IMI UCITS Acc (IE00BKM4GZ66)",      "10%", "€30 000",
     "chat:message2489 — VEU/SPY пробой"),
    ("",                 "IWMO — MSCI World Momentum UCITS Acc (IE00BP3QZ825)", "8%",  "€24 000",
     "chat:message97 — факторный оверлей"),

    ("Облигации (EUR)",  None,          "8%",  "€24 000",
     "Минимальный буфер; подушка — €800k в банке"),
    ("",                 "VAGF — Global Agg Bond EUR Hedged Acc (IE00BG47KH54)", "8%",  "€24 000",
     "chat:message2414 — без длинных Трежерис"),

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
     "Только на расчёты; подушка = банк"),
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
        "Синтез по философии канала «Капитал» (SGCapital). "
        "Портфель: старт €300k, пополнения €25k/кв (40 взносов = +€1М). "
        "Прочие активы: vivienda habitual €1.5M, банковские счета €800k. "
        "Общее состояние на старте ≈ €2.6M. "
        "Юрисдикция — Comunidad Valenciana, валюта — EUR. "
        "UCITS Acc на EU-биржах.",
        subtitle_style))

    story.append(Paragraph("Итоговая аллокация", h2_style))
    story.append(build_table())

    story.append(Paragraph("Ключевые решения", h2_style))
    bullets = [
        "<b>Equities 62% — портфель = чистый growth engine.</b> "
        "У вас €800k в банке (31% общего состояния) + €1.5M недвижимость. "
        "Портфель — единственный компонент, задача которого генерировать "
        "доходность. Бонды/кэш в нём — избыточны и дублируют банк. "
        "Каноническая equity-база канала: chat:message42, chat:message1310.",
        "<b>США 23% vs ex-US 31% (EXUS 21% + EMIM 10%).</b> "
        "chat:message2489 (январь 2026): иностранцы в акциях США у "
        "исторических максимумов, VEU/SPY впервые с 2011 тестирует "
        "200-недельную. США < 40% equity-блока — осознанный недовес.",
        "<b>Облигации урезаны до 8%.</b> Один фонд: VAGF (EUR hedged "
        "global aggregate). Зачем: 40 квартальных взносов создают "
        "«поток денег», который выполняет функцию бонд-части (DCA = "
        "покупка в просадках). €800k на счёте — ваш реальный буфер.",
        "<b>Драгметаллы 17%.</b> Структурный цикл из chat:message2229 "
        "(янв 2024) в 2025 дал +170% по золотодобытчикам; на 10y выходить "
        "преждевременно.",
        "<b>Крипта 5%, BTCE (XETRA).</b> Securitized ETP → учёт через "
        "Modelo 720, не 721.",
        "<b>Ребалансировка — только через пополнения.</b> €25k/кв → "
        "в недовешенный блок. Продажи (CGT 19–28%) — крайняя мера "
        "при дрифте ≥7 п.п. (chat:message559).",
    ]
    for b in bullets:
        story.append(Paragraph("• " + b, body_style))

    story.append(Paragraph(
        "Patrimonio на ВСЁ состояние (CV, vivienda habitual)", h2_style))
    story.append(Paragraph(
        "<b>База Patrimonio = всё имущество на 31.12.</b> "
        "CV exento €500k, VH exento €300k (итого «бесплатно» €800k). "
        "Bonificación нет, шкала 0.2–3.5%. ITSGF (федеральный) "
        "зачитывается против Patrimonio — двойного удара нет.",
        body_style))

    # Full-wealth Patrimonio projection
    # RE €1.5M (VH exento €300k → taxable €1.2M), bank €800k,
    # portfolio grows from €300k at +5%/yr + €100k/yr contributions.
    story.append(Paragraph(
        "Состав базы: недвижимость €1.2M (после VH −€300k) + "
        "банк €800k + портфель (растёт). Exento CV = €500k.",
        body_style))

    story.append(Paragraph(
        "Patrimonio год-за-годом (всё состояние)", h2_style))
    proj_data = [
        ["Год", "Портфель*", "Общее**", "Taxable base***",
            "Patrimonio/год"],
        ["0",   "€300k",    "€2 300k", "€1 800k",  "≈ €14 500"],
        ["1",   "€415k",    "€2 415k", "€1 915k",  "≈ €16 000"],
        ["2",   "€536k",    "€2 536k", "€2 036k",  "≈ €17 600"],
        ["3",   "€663k",    "€2 663k", "€2 163k",  "≈ €19 250"],
        ["4",   "€796k",    "€2 796k", "€2 296k",  "≈ €21 000"],
        ["5",   "€936k",    "€2 936k", "€2 436k",  "≈ €22 800"],
        ["6",   "€1 083k",  "€3 083k", "€2 583k",  "≈ €24 700"],
        ["7",   "€1 237k",  "€3 237k", "€2 737k",  "≈ €26 700"],
        ["8",   "€1 399k",  "€3 399k", "€2 899k",  "≈ €28 800"],
        ["9",   "€1 569k",  "€3 569k", "€3 069k",  "≈ €31 000"],
        ["10",  "€1 747k",  "€3 747k", "€3 247k",  "≈ €35 700"],
    ]
    proj_widths = [12 * mm, 25 * mm, 25 * mm, 30 * mm, 48 * mm]
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
        "<i>* Портфель: +5%/год на базу + €100k/год взносов. "
        "** Общее = RE €1.2M (после VH) + банк €800k + портфель. "
        "RE и банк приняты стабильными. "
        "*** Taxable = общее − exento CV €500k.</i>",
        body_style))
    story.append(Paragraph(
        "<b>Кумулятивно за 10 лет: ≈ €258 000 Patrimonio.</b> "
        "Это 15–20% от суммарных взносов в портфель (€1.3M). "
        "Patrimonio — второй по величине расход после самих инвестиций. "
        "Вы уже платите ~€14 500/год прямо сейчас.",
        body_style))

    story.append(Paragraph(
        "Что делать (переезд исключён):", body_style))
    val_actions = [
        "<b>VH exento уже применяется</b> — проверить, что "
        "vivienda habitual корректно задекларирована как таковая. "
        "Без неё taxable base была бы на €300k выше → "
        "дополнительно ~€3 000–4 000/год.",
        "<b>Plan de Pensiones (€1 500/год).</b> "
        "Уменьшает и IRPF, и Patrimonio base. "
        "За 10 лет: −€15k из базы → экономия ~€1 500–2 000 "
        "кумулятивно по Patrimonio + экономия по IRPF.",
        "<b>Unit-linked (seguro de vida de ahorro).</b> "
        "Испанский life-insurance wrapper с UCITS-корзиной внутри. "
        "Преимущества: (а) IRPF откладывается до снятия, "
        "(б) в некоторых конфигурациях уменьшает Patrimonio base "
        "(спорно с 2022 — проверять с gestor). "
        "Стоит рассматривать, когда годовой Patrimonio > €20k "
        "(то есть уже сейчас). Стоимость обёртки: ~0.3–0.5%/год TER.",
        "<b>Банковские €800k.</b> Они сидят в базе Patrimonio И "
        "при этом теряют на инфляции (~2–3%/год = €16–24k/год "
        "реальных потерь). Перемещение части в портфель не уменьшит "
        "Patrimonio (актив остаётся), но хотя бы даст доходность. "
        "€800k в банке при €2.6M состояния = 31% кэша — чрезмерно. "
        "Рекомендация канала: «подушка безопасности» = 6–12 месяцев "
        "расходов. Если расходы ~€100k/год → достаточно €100–150k.",
        "<b>Контроль весов через DCA.</b> Квартальных €25k "
        "достаточно для штатных ребалансов. Продажи (CGT 19–28%) — "
        "только при дрифте ≥7 п.п.",
    ]
    for b in val_actions:
        story.append(Paragraph("• " + b, body_style))

    story.append(Paragraph("Логика квартальных взносов €25 000", h2_style))
    dca = [
        "Каждый квартал: посмотреть текущие веса блоков vs целевые в таблице выше.",
        "Весь €25 000 распределить в блоки, которые <b>ниже</b> цели, "
        "пропорционально размеру «дыры». Не продавать ничего.",
        "Если все блоки в пределах ±2 п.п. от цели — распределить взнос по "
        "целевым весам (62% в акции, 8% в бонды, 17% в драгметаллы, "
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
