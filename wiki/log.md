# Лог операций вики SGCapital

## [2026-04-16] ingest | Первичная загрузка: 1996 сообщений (2017-04-04 — 2026-04-14)

Создана вики по паттерну Карпаты LLM Wiki. Выполнено:

- Парсинг `messages.html`, `messages2.html`, `messages3.html` → `tools/chat.jsonl` (1996 записей).
- Тематический индекс `INDEX.md` — 26 тем, покрытие 92%.
- `CLAUDE.md` — конституция базы знаний.
- Скрипт `tools/build_wiki.py` — генератор вики-страниц с сохранением ручного контента.
- Сгенерировано **23 страницы** в `wiki/`:
  - 8 concepts, 7 entities, 4 theses, 4 timeline
- Ручной синтез написан для seed-страниц:
  `advisor-commissions`, `gold`, `active-mgmt-passive-instruments`, `rebalancing`.
- `wiki/index.md`, `wiki/log.md`, `wiki/overview.md` — служебные файлы.

Исключены из вики (scope filter): рубль, ОФЗ, российский рынок акций,
ИИС, ключевая ставка ЦБ РФ.
