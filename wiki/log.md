# Журнал ingestion

Хронологическая запись сессий, в которых что-то добавлялось или менялось в `wiki/`. Формат: дата — кратко, что сделано, какие страницы затронуты. Новые записи — сверху.

---

## 2026-04-15 — автоматизация ingest + forecast track record

**Автор:** Claude (та же сессия, ветка `claude/migrate-telegram-chat-NRzed`).

**Контекст.** После первого ingestion мы работали с корпусом как с «замороженным» документом: 1996 сообщений до 2026-04-14, дальше — тишина. Задача этой записи — поставить **автоматический догон** новых постов с публичного превью канала `t.me/s/sgcapital`, чтобы при любом новом заходе в репо корпус был актуален, и записать первое содержательное табло прогнозов канала.

**Ключевое архитектурное решение.** После этого ingest'а `tools/chat.jsonl` **становится каноничным источником правды**. `messages*.html` — замороженный архив, не перегенерируется. В корпусе теперь сосуществуют две когорты записей:

- **архивная** — `msg_id = messageN`, `source = messages*.html` (1996 штук);
- **онлайн** — `msg_id = tg:<N>`, `source = t.me/s/sgcapital` (дописываются автоматикой).

Все инструменты (`build_index.py`, `build_wiki.py`, будущие) умеют работать с обеими когортами одинаково.

**Что сделано:**

- Написан `tools/fetch_chat.py` — инкрементальный парсер `t.me/s/sgcapital`. Читает max `tg:<N>` из корпуса, парсит превью-страницу, для новых постов опционально прогоняет картинки через Claude Haiku 4.5 (`ANTHROPIC_API_KEY`) и дописывает JSONL-строки в `chat.jsonl`. Поддерживает `--dry-run`, `--limit`, `--before`. Парсер проверен на синтетическом HTML-фикстуре.
- Добавлен `.github/workflows/fetch-chat.yml` — CI-воркфлоу: `cron 17 6 * * *` + `workflow_dispatch`. Запускает `fetch_chat.py`, проверяет `git diff tools/chat.jsonl`, при наличии изменений перезапускает `build_index.py` и `build_wiki.py`, открывает PR на `main` через `peter-evans/create-pull-request@v6` (ветка `bot/daily-ingest`, метки `automated`, `ingest`).
- В `tools/build_index.py` и `tools/build_wiki.py` добавлено чтение нового поля `media_description` при матчинге ключевых слов — картинки, описанные моделью, теперь тоже тегируются.
- В `tools/build_wiki.py` добавлена новая тема `forecasts` в `WIKI_TOPICS` — чтобы страница `forecast-track-record.md` имела свой автоген-сидекар.
- `tools/build_wiki.py` теперь корректно генерирует ссылки для обеих когорт: `messageN` → `../../messages.html#...`, `tg:N` → `https://t.me/sgcapital/N`.
- Написана `wiki/principles/forecast-track-record.md` — послужной список прогнозов канала за 2024–2025 с табло: 5 сбылись, 2 не сбылись, 1 частично, 1 рано судить. Там же методология и правило «строки не удалять».
- `CLAUDE.md` обновлён: §1 описывает новую реальность с двумя когортами и заморозкой HTML, §3 документирует `fetch_chat.py` и воркфлоу, §5 отделяет авторизованные append'ы от ручных правок `chat.jsonl`.
- Перегенерированы `wiki/_sources/*.md` (уже 16 файлов — добавился `forecasts.md`) и `wiki/index.md`.

**Что требуется от человека, чтобы автоматика заработала полностью:**

1. Смержить эту ветку в `main`, иначе GitHub Actions `cron` не начнёт тикать (schedule работает только с дефолтной ветки). `workflow_dispatch` — работает и из этой ветки.
2. Положить `ANTHROPIC_API_KEY` в Secrets репозитория — без него картинки будут сохраняться как URL, без текстовых описаний.
3. Проверить, что у GitHub Actions стоит разрешение «Allow GitHub Actions to create pull requests» (Settings → Actions → General), иначе `peter-evans/create-pull-request` получит 403.

**Затронутые файлы (новые):**

- `tools/fetch_chat.py`
- `.github/workflows/fetch-chat.yml`
- `wiki/principles/forecast-track-record.md`
- `wiki/_sources/forecasts.md` (автоген)

**Затронутые файлы (изменены):**

- `CLAUDE.md`
- `tools/build_index.py`
- `tools/build_wiki.py`
- `wiki/log.md` (эта запись)
- `wiki/index.md` (автоген, обновление)

**Что НЕ тронуто:** `messages*.html`, `tools/chat.jsonl` (сейчас ещё без новых строк — автоматика впервые дописывает в него в CI, не в этой сессии, чтобы коммит был строго про инфраструктуру), `tools/parse_chat.py`, `INDEX.md`.

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
