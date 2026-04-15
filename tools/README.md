# tools/

Утилиты для превращения Telegram-экспорта канала «Капитал» (SGCapital)
в удобную базу знаний.

## Файлы

| Файл | Назначение |
|---|---|
| `parse_chat.py` | Парсит `messages*.html` → чистый JSONL `tools/chat.jsonl` (дата, время, автор, текст, медиа, ссылка на исходное сообщение). |
| `build_index.py` | Читает `tools/chat.jsonl` и собирает тематический индекс `INDEX.md` по ключевым словам. |
| `chat.jsonl` | Корпус сообщений (1 JSON-объект на строку). Генерируется; под git для удобства поиска / grep. |

## Как пересобрать

```bash
pip install beautifulsoup4 lxml
python3 tools/parse_chat.py     # messages*.html -> tools/chat.jsonl
python3 tools/build_index.py    # tools/chat.jsonl -> INDEX.md
```

## Формат записи в `chat.jsonl`

```json
{
  "id": 1,
  "date": "2017-04-04",
  "time": "23:07:37",
  "author": "Капитал",
  "forwarded_from": null,
  "text": "О чем этот канал? ...",
  "media": null,
  "source": "messages.html",
  "msg_id": "message3"
}
```

Ссылка на оригинальное сообщение в экспорте: `<source>#<msg_id>`,
например `messages.html#message3`.

## Как добавить / изменить темы

Темы описаны в `build_index.py` в списке `THEMES` как кортежи
`(ключ, заголовок, [ключевые_слова])`. Ключевые слова ищутся как
подстроки по lowercase-версии текста, поэтому можно писать как
`"офз"`, `"облигац"`, так и английские варианты (`"etf"`, `"s&p"`).
Одно сообщение попадает во все темы, чьи ключевые слова встретились.

После правок запустите `python3 tools/build_index.py` заново.
