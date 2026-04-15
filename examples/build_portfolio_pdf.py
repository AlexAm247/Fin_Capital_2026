#!/usr/bin/env python3
"""Generate a one-page PDF of the $300k allocation table.

Output: examples/portfolio-300k-usd.pdf

Source of truth for the numbers — examples/portfolio-300k-usd.md (the synthesis
document from the channel's philosophy). This script is a presentation helper
only; it does not re-derive weights.
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
ROWS = [
    ("Глобальные акции", None,          "50%", "$150 000",
     "Долгосрочный генератор доходности"),
    ("",                 "VTI — US broad",            "18%", "$54 000",
     "chat:message2489 — недовес США vs капвесу"),
    ("",                 "VEA — Developed ex-US",     "18%", "$54 000",
     "chat:message2405 — разворот Европы"),
    ("",                 "VWO — Emerging markets",    "8%",  "$24 000",
     "chat:message2489 — VEU/SPY пробой"),
    ("",                 "MTUM — US momentum",        "6%",  "$18 000",
     "chat:message97 — факторный оверлей"),

    ("Короткие облигации", None,        "15%", "$45 000",
     "Подушка риска, только короткая дюрация"),
    ("",                 "BSV — short US IG/Treas",   "10%", "$30 000",
     "chat:message2414 — длинные Трежерис не берём"),
    ("",                 "BNDX — int'l IG short",     "5%",  "$15 000",
     "Валютная диверсификация бонд-части"),

    ("Драгметаллы",      None,          "18%", "$54 000",
     "Структурная защитная корзина"),
    ("",                 "GLD — gold",                "9%",  "$27 000",
     "chat:message56, chat:message2229"),
    ("",                 "SLV — silver",              "4%",  "$12 000",
     "Опережает золото на поздней фазе цикла"),
    ("",                 "GDX — gold miners",         "2%",  "$6 000",
     "«Рычаг» к золоту"),
    ("",                 "PALL — palladium",          "2%",  "$6 000",
     "chat:message2453 — просыпается последним"),
    ("",                 "PPLT — platinum",           "1%",  "$3 000",
     "chat:message56 — иная фундаменталка"),

    ("Промсырьё / энергия", None,       "7%",  "$21 000",
     "Инфляционный хедж помимо драгов"),
    ("",                 "COPX — copper miners",      "4%",  "$12 000",
     "chat:message2414 — медь пробивает сопротивление"),
    ("",                 "XLE — energy",              "3%",  "$9 000",
     "chat:message2414 — «нефть я бы не хоронил»"),

    ("Крипта",           None,          "5%",  "$15 000",
     "Структурный тезис + инфляционный бенефициар"),
    ("",                 "IBIT — spot BTC ETF",       "5%",  "$15 000",
     "chat:message2227, chat:message2414"),

    ("Кэш / money market", None,        "5%",  "$15 000",
     "Пыль для ребалансировок"),
    ("",                 "SGOV — short T-bills",      "5%",  "$15 000",
     "≈ ставка ФРС, ликвидность"),
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

    col_widths = [78 * mm, 15 * mm, 22 * mm, 65 * mm]
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
        "Модельный портфель на $300 000", title_style))
    story.append(Paragraph(
        "Синтез по философии канала «Капитал» (SGCapital) · данные корпуса по состоянию на 27 января 2026",
        subtitle_style))

    story.append(Paragraph("Итоговая аллокация", h2_style))
    story.append(build_table())

    story.append(Paragraph("Ключевые решения", h2_style))
    bullets = [
        "<b>Equities 50%, внутри США меньше половины блока.</b> "
        "Прямое следствие поста 27 января 2026 (chat:message2489): аллокация "
        "иностранцев в акции США у исторических максимумов, VEU/SPY впервые "
        "с 2011 тестирует 200-недельную.",
        "<b>Драгметаллы 18% — осознанно много.</b> Структурный цикл из "
        "chat:message2229 (январь 2024) в 2025 дал +170% по GDX/SIL и +38% "
        "по PALL; выходить пока рано.",
        "<b>Никаких длинных Трежерис.</b> chat:message2414 (июнь 2025): "
        "«для долгосрочного портфеля не выглядят привлекательно». "
        "Только короткая дюрация.",
        "<b>Крипта через спотовый BTC-ETF.</b> Структурный тезис канала с "
        "2017, валидированный институционализацией в январе 2024.",
        "<b>Ребалансировка — раз в год либо при отклонении ≥5 п.п.</b> "
        "Правило из chat:message559 (2018-09-04).",
    ]
    for b in bullets:
        story.append(Paragraph("• " + b, body_style))

    story.append(Paragraph("Чего в портфеле НЕТ и почему", h2_style))
    not_in = [
        "<b>RU-активов</b> — по CLAUDE.md §2.2 и отсутствию свежей рамки канала.",
        "<b>Длинных Трежерис</b> (TLT/EDV/ZROZ) — chat:message2414.",
        "<b>Хедж-фондов, структурных нот, ДУ с комиссией ≥1%</b> — "
        "chat:message5, chat:message121, chat:message131.",
        "<b>Отдельных акций-хайпов</b> — chat:message154: 4% акций "
        "создают почти всё богатство рынка, угадать их — лотерея.",
        "<b>Шортов/инверсных ETF</b> — не играем против тренда "
        "(chat:message2329, chat:message2467).",
    ]
    for b in not_in:
        story.append(Paragraph("• " + b, body_style))

    story.append(Paragraph(
        "<b>Дисклеймер.</b> Это не инвестиционная рекомендация. Документ — "
        "синтез явных высказываний канала «Капитал» со ссылками на "
        "конкретные сообщения в tools/chat.jsonl. Сам канал в "
        "chat:message860 подчёркивает: «аллокация активов для каждого "
        "инвестора — дело очень индивидуальное». Решение — ваше. "
        "Полный разбор с лесенкой входа, правилами ребалансировки и "
        "списком точек пересмотра — в examples/portfolio-300k-usd.md.",
        disclaimer_style))

    doc.build(story)


if __name__ == "__main__":
    out = Path(__file__).parent / "portfolio-300k-usd.pdf"
    build_pdf(out)
    print(f"wrote {out}")
