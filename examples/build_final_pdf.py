#!/usr/bin/env python3
"""Final comprehensive portfolio PDF — all-in-one document.

Output: examples/portfolio-final.pdf
"""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
)

# --- fonts ---
for name, path in [
    ("DJS", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ("DJS-B", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]:
    if Path(path).exists():
        pdfmetrics.registerFont(TTFont(name, path))
FR, FB = "Helvetica", "Helvetica-Bold"
try:
    pdfmetrics.getFont("DJS")
    FR, FB = "DJS", "DJS-B"
except:
    pass

styles = getSampleStyleSheet()
T = ParagraphStyle("t", parent=styles["Title"], fontName=FB, fontSize=16, leading=20, spaceAfter=3, textColor=colors.HexColor("#0b2545"))
SUB = ParagraphStyle("sub", parent=styles["Normal"], fontName=FR, fontSize=9, leading=12, textColor=colors.HexColor("#555"), spaceAfter=8)
H2 = ParagraphStyle("h2", parent=styles["Heading2"], fontName=FB, fontSize=11, leading=14, spaceBefore=8, spaceAfter=3, textColor=colors.HexColor("#0b2545"))
H3 = ParagraphStyle("h3", parent=styles["Heading3"], fontName=FB, fontSize=10, leading=13, spaceBefore=6, spaceAfter=2, textColor=colors.HexColor("#1a3a5c"))
B = ParagraphStyle("b", parent=styles["Normal"], fontName=FR, fontSize=8, leading=11, spaceAfter=4)
SM = ParagraphStyle("sm", parent=styles["Normal"], fontName=FR, fontSize=7, leading=10, textColor=colors.HexColor("#777"), spaceBefore=6)

def tbl(data, widths, has_header=True):
    t = Table(data, colWidths=widths, repeatRows=1 if has_header else 0)
    cmds = [
        ("FONTNAME", (0,0), (-1,-1), FR), ("FONTSIZE", (0,0), (-1,-1), 7),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#ccc")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#f5f5f5"), colors.white]),
    ]
    if has_header:
        cmds += [
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0b2545")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("FONTNAME", (0,0), (-1,0), FB), ("FONTSIZE", (0,0), (-1,0), 7),
        ]
    t.setStyle(TableStyle(cmds))
    return t

def build(out):
    doc = SimpleDocTemplate(str(out), pagesize=A4,
        leftMargin=14*mm, rightMargin=14*mm, topMargin=14*mm, bottomMargin=14*mm)
    s = []
    p = lambda txt, st=B: s.append(Paragraph(txt, st))
    sp = lambda: s.append(Spacer(1, 3))

    # ===== PAGE 1: PROFILE + ALLOCATION =====
    p("Инвестиционный план · €300k · Испания / CV / 10 лет", T)
    p("Канал «Капитал» (SGCapital) · апрель 2026. Полная версия: тикеры, ISIN, "
      "суммы, пошаговый вход, DCA-протокол, Patrimonio на всё состояние, "
      "бюджет расходов и план оптимизации.", SUB)

    p("1. Профиль инвестора", H2)
    s.append(tbl([
        ["Параметр", "Значение"],
        ["Портфель (старт)", "€300 000"],
        ["Пополнение", "€25 000 / квартал (40 взносов = €1 000 000)"],
        ["Горизонт", "10 лет"],
        ["Недвижимость (VH)", "€1 500 000 (vivienda habitual)"],
        ["Банковские счета", "€800 000"],
        ["Общее состояние (старт)", "€2 600 000"],
        ["Юрисдикция", "Comunidad Valenciana"],
        ["Валюта учёта и расходов", "EUR"],
        ["Крипта", "ОК"],
        ["Переезд из CV", "Исключён"],
    ], [55*mm, 125*mm]))
    sp()

    p("2. Итоговая аллокация портфеля", H2)
    alloc = [
        ["Тикер", "Название / ISIN", "%", "EUR", "TER"],
        # equities
        ["CSPX", "iShares Core S&P 500 UCITS Acc\nIE00B5BMR087", "23%", "€69 000", "0.07%"],
        ["EXUS", "iShares MSCI World ex-USA UCITS Acc\nIE00BKBF6H24", "21%", "€63 000", "0.15%"],
        ["EMIM", "iShares Core MSCI EM IMI UCITS Acc\nIE00BKM4GZ66", "10%", "€30 000", "0.18%"],
        ["IWMO", "iShares Edge MSCI World Momentum UCITS Acc\nIE00BP3QZ825", "8%", "€24 000", "0.30%"],
        # bonds
        ["VAGF", "Vanguard Global Agg Bond EUR Hedged Acc\nIE00BG47KH54", "8%", "€24 000", "0.10%"],
        # precious metals
        ["SGLN", "iShares Physical Gold ETC\nIE00B4ND3602", "9%", "€27 000", "0.12%"],
        ["SSLN", "iShares Physical Silver ETC\nIE00B4NCWG09", "3%", "€9 000", "0.20%"],
        ["GDGB", "VanEck Gold Miners UCITS ETF\nIE00BQQP9F84", "2%", "€6 000", "0.53%"],
        ["PHPD", "WisdomTree Physical Palladium\nJE00B1VS3002", "2%", "€6 000", "0.49%"],
        ["PHPT", "WisdomTree Physical Platinum\nJE00B1VS2W53", "1%", "€3 000", "0.49%"],
        # commodities
        ["COPG", "Global X Copper Miners UCITS ETF\nIE000NXF88V8", "3%", "€9 000", "0.65%"],
        ["IUES", "iShares S&P 500 Energy Sector UCITS\nIE00B42NKQ00", "2%", "€6 000", "0.15%"],
        # crypto
        ["BTCE", "21Shares Bitcoin Core ETP\nCH1199067674 (XETRA)", "5%", "€15 000", "0.21%"],
        # cash
        ["XEON", "Xtrackers II EUR Overnight Rate Swap\nLU0290358497", "3%", "€9 000", "0.10%"],
        # total
        ["", "ИТОГО", "100%", "€300 000", "0.18%*"],
    ]
    s.append(tbl(alloc, [14*mm, 72*mm, 11*mm, 18*mm, 13*mm]))
    p("<i>* Средневзвешенный TER портфеля. На старте ≈ €540/год. "
      "К году 10 (~€1.75M портфель) ≈ €3 150/год.</i>", SM)

    # ===== PAGE 2: ENTRY PLAN + DCA =====
    p("3. Пошаговый план входа (месяц 1)", H2)
    entry = [
        ["Шаг", "Действие", "Детали"],
        ["1", "Перевести €300 000 на Exante", "Счёт уже открыт и верифицирован. "
         "SEPA-перевод из банка → Exante. Обычно T+1."],
        ["2", "Проверить доступность тикеров", "Вбить каждый ISIN из таблицы в поиск Exante. "
         "Все 14 — UCITS на XETRA/LSE, должны быть доступны. "
         "Если какой-то отсутствует — см. раздел «Выбор брокера»."],
        ["3", "Купить 14 позиций", "Ордера limit, не market. Порядок не важен — "
         "всё покупается в один день. Суммы из таблицы выше."],
        ["4", "Проверить Modelo 720", "Порог €50k пробит сразу. Декларация до 31 марта "
         "следующего года. Exante не генерирует отчёт 720 автоматически — "
         "скачать годовую выписку и передать gestor'у. "
         "BTCE идёт в категорию «ценные бумаги» (720), не в 721."],
        ["5", "Оформить Plan de Pensiones", "У любого банка/страховой в ES. Лимит €1 500/год. "
         "Первый взнос — сразу, далее автоплатёж."],
    ]
    s.append(tbl(entry, [10*mm, 42*mm, 128*mm]))
    sp()

    p("4. DCA-протокол (каждый квартал, €25 000)", H2)
    p("Раз в квартал (январь, апрель, июль, октябрь) выполнить 3 шага:", B)
    dca = [
        ["Шаг", "Действие"],
        ["1. Снимок", "Открыть портфель у брокера. Записать текущий % каждого блока "
         "(акции / бонды / драгметаллы / commodities / крипта / кэш)."],
        ["2. Дефицит", "Сравнить с целевыми (62/8/17/5/5/3). Вычислить, какие блоки "
         "ниже цели и на сколько."],
        ["3. Покупка", "Весь €25 000 направить в недовешенные блоки, пропорционально "
         "дефициту. Если все блоки ±2 п.п. от цели — купить по целевым весам. "
         "НИЧЕГО НЕ ПРОДАВАТЬ."],
    ]
    s.append(tbl(dca, [20*mm, 160*mm]))
    sp()
    p("<b>Жёсткий ребаланс (с продажами):</b> раз в год, в январе, "
      "если какой-то блок дрифтанул ≥7 п.п. от цели И квартальных "
      "взносов не хватило это исправить. Помнить: продажа = CGT 19–28%.", B)

    # ===== PAGE 3: PATRIMONIO =====
    p("5. Patrimonio — полная картина (всё состояние)", H2)
    p("База = RE €1.2M (VH €1.5M − exento €300k) + банк €800k + портфель. "
      "Exento CV = €500k. Шкала 0.2–3.5%.", B)
    pat = [
        ["Год", "Портфель", "Всего", "Taxable", "Patrimonio/год", "Нарастающим"],
        ["0", "€300k", "€2.30M", "€1.80M", "€14 500", "€14 500"],
        ["1", "€415k", "€2.42M", "€1.92M", "€16 000", "€30 500"],
        ["2", "€536k", "€2.54M", "€2.04M", "€17 600", "€48 100"],
        ["3", "€663k", "€2.66M", "€2.16M", "€19 250", "€67 350"],
        ["4", "€796k", "€2.80M", "€2.30M", "€21 000", "€88 350"],
        ["5", "€936k", "€2.94M", "€2.44M", "€22 800", "€111 150"],
        ["6", "€1.08M", "€3.08M", "€2.58M", "€24 700", "€135 850"],
        ["7", "€1.24M", "€3.24M", "€2.74M", "€26 700", "€162 550"],
        ["8", "€1.40M", "€3.40M", "€2.90M", "€28 800", "€191 350"],
        ["9", "€1.57M", "€3.57M", "€3.07M", "€31 000", "€222 350"],
        ["10", "€1.75M", "€3.75M", "€3.25M", "€35 700", "€258 050"],
    ]
    s.append(tbl(pat, [11*mm, 22*mm, 22*mm, 22*mm, 30*mm, 30*mm]))
    sp()

    # ===== PAGE 4: COST BUDGET + OPTIMIZATION =====
    p("6. Бюджет расходов (год 0 → год 10)", H2)
    costs = [
        ["Статья", "Год 0", "Год 5", "Год 10", "За 10 лет"],
        ["Patrimonio (CV)", "€14 500", "€22 800", "€35 700", "€258 000"],
        ["TER портфеля (0.18%)", "€540", "€1 680", "€3 150", "≈ €18 000"],
        ["Брокерские комиссии (Exante)*", "€100", "€100", "€100", "≈ €1 000"],
        ["Инфляционные потери банк €800k**", "€20 000", "€20 000", "€20 000", "€200 000"],
        ["ИТОГО drag", "€35 140", "€44 580", "€58 950", "≈ €477 000"],
    ]
    s.append(tbl(costs, [52*mm, 22*mm, 22*mm, 22*mm, 25*mm]))
    p("<i>* Exante: ~€2/сделка × 14 позиций × ~4 покупки/год ≈ €100. "
      "** Инфляция 2.5%/год на €800k неинвестированных = €20k/год реальных потерь.</i>", SM)
    sp()

    p("7. План оптимизации расходов (конкретные действия)", H2)

    p("Действие 1: Сократить банковский кэш с €800k до €150k", H3)
    p("€650k из банка → в портфель (по тем же весам 62/8/17/5/5/3). "
      "Patrimonio НЕ меняется (актив в базе тот же). "
      "Но: €650k начинают генерировать ~5%/год = <b>€32 500/год</b> вместо нуля. "
      "За 10 лет при 5% compound: <b>+€390 000 дополнительной стоимости</b> "
      "vs лежания в банке. Это самое крупное решение в этом документе.", B)
    opt1 = [
        ["Тикер", "Доп. покупка (€650k × вес)", "Итого с €300k"],
        ["CSPX", "€149 500", "€218 500"],
        ["EXUS", "€136 500", "€199 500"],
        ["EMIM", "€65 000", "€95 000"],
        ["IWMO", "€52 000", "€76 000"],
        ["VAGF", "€52 000", "€76 000"],
        ["SGLN", "€58 500", "€85 500"],
        ["SSLN", "€19 500", "€28 500"],
        ["GDGB", "€13 000", "€19 000"],
        ["PHPD", "€13 000", "€19 000"],
        ["PHPT", "€6 500", "€9 500"],
        ["COPG", "€19 500", "€28 500"],
        ["IUES", "€13 000", "€19 000"],
        ["BTCE", "€32 500", "€47 500"],
        ["XEON", "€19 500", "€28 500"],
        ["ИТОГО", "€650 000", "€950 000"],
    ]
    s.append(tbl(opt1, [16*mm, 55*mm, 55*mm]))
    sp()

    p("Действие 2: Plan de Pensiones — €1 500/год", H3)
    p("Оформить у любого банка или страховой в Испании. "
      "Экономия IRPF: при ставке 37% (доход ~€60k+) → <b>€555/год</b>. "
      "Уменьшение базы Patrimonio: −€1 500/год → экономия <b>≈ €15–20/год</b> "
      "(маргинальная ставка 0.9–1.3%). "
      "За 10 лет: <b>€5 550 экономии IRPF + €150–200 экономии Patrimonio</b>. "
      "Усилие: 1 час на оформление + автоплатёж.", B)
    sp()

    p("Действие 3: Unit-linked (seguro de vida de ahorro)", H3)
    p("Обёртка life-insurance с UCITS-корзиной внутри. "
      "Провайдеры в ES: Aegon, Caser, Mapfre, Zurich. "
      "Стоимость: TER обёртки 0.3–0.5%/год поверх TER фондов.", B)
    p("<b>Экономия:</b> IRPF на доходы портфеля откладывается до снятия "
      "(аналог Acc, но на уровне всего портфеля). "
      "Patrimonio: спорно с 2022 — ранее unit-linked оценивался "
      "по стоимости выкупа (ниже NAV), сейчас по NAV. "
      "<b>Вердикт:</b> стоит обсудить с gestor'ом при годовом "
      "Patrimonio > €20k (ваш случай — €14.5k уже сейчас). "
      "Потенциальная экономия: <b>€0–5 000/год</b> по IRPF в зависимости "
      "от реализации доходов.", B)
    sp()

    p("Действие 4: Проверить декларацию Vivienda Habitual", H3)
    p("Убедиться, что жильё (€1.5M) задекларировано как VH в Modelo 100 (IRPF). "
      "Exento VH = €300k — без неё taxable base Patrimonio на €300k выше → "
      "<b>+€3 000–4 000/год</b>. Усилие: проверка с gestor, 30 минут.", B)
    sp()

    p("Действие 5: Выбор брокера (BY-паспорт + ES-резиденция)", H3)
    p("Interactive Brokers недоступен с белорусским паспортом. "
      "У вас уже есть верифицированный счёт в <b>Exante</b> (Мальта) — "
      "это основной рабочий вариант.", B)
    broker = [
        ["Брокер", "BY-паспорт", "Плюсы", "Минусы", "14 тикеров?"],
        ["Exante (Malta)", "✅ Уже есть", "Все биржи EU, XETRA/LSE, "
         "крипто-ETP, US ETF", "~€1.50–3/сделка, "
         "нет авто-720", "Да (проверить)"],
        ["Saxo Bank (DK)", "⚠ Проверять", "Широкий ассортимент UCITS, "
         "есть 720-отчёт", "Мин. депозит, "
         "комиссия выше", "Да"],
        ["Freedom24 (CY)", "✅ Принимает", "CIS-friendly, "
         "низкие комиссии", "Узкий ассорт. ETC, "
         "репутация", "Нет (10/14)"],
        ["DEGIRO (NL)", "⚠ Проверять", "Бесплатные core ETF", "Нет PHPD/PHPT/"
         "BTCE", "Нет (11/14)"],
    ]
    s.append(tbl(broker, [28*mm, 22*mm, 42*mm, 32*mm, 22*mm]))
    p("<b>Рекомендация: Exante.</b> Счёт уже верифицирован, "
      "все биржи EU доступны, включая XETRA для BTCE. "
      "Единственный минус — Modelo 720 заполняется вручную "
      "(gestor берёт годовую выписку). "
      "Резервный вариант: Saxo Bank (проверить приём BY-паспорта).", B)
    sp()

    # ===== SUMMARY TABLE =====
    p("8. Итоговая карта оптимизации", H2)
    summary = [
        ["Действие", "Усилие", "Экономия / доп. доход за 10 лет"],
        ["Сократить банк €800k → €150k", "1 день (перевод + покупки)", "+€390 000 (compound growth)"],
        ["Plan de Pensiones €1 500/г", "1 час + автоплатёж", "+€5 700 (IRPF + Patrimonio)"],
        ["Unit-linked (если gestor одобрит)", "Переговоры, 2–3 недели", "+€0–50 000 (зависит от структуры)"],
        ["Проверить VH декларацию", "30 минут с gestor", "+€30 000–40 000 (если VH не задекларирована)"],
        ["Exante (vs дорогой банк-брокер)", "Счёт уже есть", "+€5 000–10 000 (vs банковский 0.5–1% сделка)"],
    ]
    s.append(tbl(summary, [52*mm, 40*mm, 65*mm]))
    sp()

    p("9. Чего в портфеле НЕТ", H2)
    for item in [
        "<b>US-domiciled ETF</b> — PRIIPs + 15% US WHT",
        "<b>Длинных Трежерис</b> (TLT/EDV/ZROZ) — chat:message2414",
        "<b>ДУ / хедж-фонды / структурные ноты с комиссией ≥1%</b> — chat:message5, 121, 131",
        "<b>Отдельных акций</b> — chat:message154 (4% акций = всё богатство рынка)",
        "<b>Шортов / инверсных ETF</b> — chat:message2329, 2467",
        "<b>RU-активов</b> — вне скоупа",
    ]:
        p("• " + item, B)

    p("<b>Дисклеймер.</b> Не является инвестиционной или налоговой "
      "рекомендацией. Синтез высказываний канала «Капитал» + "
      "технические ограничения ES retail. Patrimonio / Modelo 720 / IRPF — "
      "ОБЯЗАТЕЛЬНО проверить с локальным gestor. "
      "Канал (chat:message860): «аллокация для каждого инвестора — "
      "дело индивидуальное».", SM)

    doc.build(s)

if __name__ == "__main__":
    o = Path(__file__).parent / "portfolio-final.pdf"
    build(o)
    print(f"wrote {o}")
