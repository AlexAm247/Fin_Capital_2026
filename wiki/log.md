# Журнал ingestion

Хронологическая запись сессий, в которых что-то добавлялось или менялось в `wiki/`. Формат: дата — кратко, что сделано, какие страницы затронуты. Новые записи — сверху.

---

## 2026-04-15 — первый ingestion

**Автор:** Claude (сессия на ветке `claude/migrate-telegram-chat-NRzed`).

**Контекст.** До этой записи в репозитории лежал сырой Telegram-экспорт канала «Капитал» (`messages*.html`), распарсенный в `tools/chat.jsonl`, и тематический указатель по ключевым словам (`INDEX.md`, собирается `tools/build_index.py`). Поверх этого — пусто. Задача сессии — ввести в эксплуатацию слой `wiki/`: конституцию, таксономию, генератор и первые сид-страницы.

**Что сделано:**

- Написан `CLAUDE.md` в корне репозитория — конституция: цель проекта, таксономия `wiki/`, правило RU-исключения, шаблон страницы, границы автономии ассистента.
- Добавлен `tools/build_wiki.py`. Делает две вещи и только их:
  1. Для каждого эвергрин-топика из встроенной таблицы `WIKI_TOPICS` — пишет хронологический список совпавших сообщений в `wiki/_sources/<topic>.md` (с ссылками обратно в `messages*.html#messageNNN`).
  2. Сканирует `wiki/**/*.md`, извлекает H1 + первую строку-тизер и регенерирует `wiki/index.md` как каталог.
- Написаны 4 сид-страницы с ручным синтезом:
  - `wiki/principles/passive-vs-active.md`
  - `wiki/principles/commissions.md`
  - `wiki/portfolio/rebalancing.md`
  - `wiki/assets/gold.md`
- Написан `wiki/overview.md` — точка входа в wiki.
- Создан этот `wiki/log.md`.
- Запущен `python3 tools/build_wiki.py` — сгенерированы `wiki/_sources/*.md` (15 топиков) и `wiki/index.md`.

**Корпус на момент записи:** 1996 сообщений, диапазон 2017-04-04 — 2026-04-14.

**Затронутые файлы (новые):**

- `CLAUDE.md`
- `tools/build_wiki.py`
- `wiki/overview.md`
- `wiki/log.md`
- `wiki/index.md` (автогенерируется)
- `wiki/_sources/*.md` (автогенерируется, 15 файлов)
- `wiki/principles/passive-vs-active.md`
- `wiki/principles/commissions.md`
- `wiki/portfolio/rebalancing.md`
- `wiki/assets/gold.md`

**Что НЕ тронуто:** `messages*.html`, `tools/chat.jsonl`, `tools/parse_chat.py`, `tools/build_index.py`, `INDEX.md` — это первоисточники и слой индекса, они не принадлежат wiki и не изменялись.

**Что дальше (для следующей сессии):**

- Наполнение страниц-резервов в таксономии по мере готовности синтеза. Приоритетные слоты, исходя из объёма первоисточников: `principles/risk-and-drawdowns`, `portfolio/asset-allocation`, `assets/equities-global`, `behavior/advisors-and-products`, `macro/crises-and-recessions`.
- Ссылки «См. также» в сид-страницах временно указывают на несуществующие файлы «в резерве». Как только эти страницы появятся, ссылки начнут разрешаться.
- Если корпус будет пополнен новыми экспортированными сообщениями — сначала перегенерировать `tools/chat.jsonl` через `tools/parse_chat.py`, затем пересобрать `INDEX.md` и `wiki/_sources/*.md` + `wiki/index.md`.
