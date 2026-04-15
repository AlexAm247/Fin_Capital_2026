#!/usr/bin/env python3
"""Incremental fetcher for the public preview of t.me/s/sgcapital (path B).

Scrapes the public web preview of the channel (no Telegram credentials
needed), extracts posts newer than what's already in `tools/chat.jsonl`,
optionally describes attached images in one-two Russian sentences via
Claude Haiku 4.5, and appends the result as JSONL rows. Designed to run
headless in CI (GitHub Actions, see `.github/workflows/fetch-chat.yml`)
or locally.

Contract:

- Never modifies existing rows in `chat.jsonl`. Only appends.
- Never touches `messages*.html` — those are a frozen archive of the
  original Telegram HTML export (see CLAUDE.md §1 and §3).
- Uses sequential integer `id` that continues the existing sequence.
- Uses `msg_id = "tg:<N>"` where N is the real Telegram post id (from
  `data-post="sgcapital/N"`). Legacy rows from the HTML export keep the
  old `msg_id = "messageN"` format — these two schemes coexist.
- Exits 0 on success even if nothing new was found. Non-zero means a
  real error (network, parse, API). CI detects "nothing new" via
  `git diff --quiet tools/chat.jsonl`.

Usage:
    python3 tools/fetch_chat.py [--dry-run] [--limit N] [--before TGID]

Env:
    ANTHROPIC_API_KEY  If set, each attached image is sent to Claude
                       Haiku 4.5 together with a short Russian prompt,
                       and the one-two sentence response is stored in
                       the new `media_description` field. Without this
                       variable the script falls back to recording only
                       the image URL.
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "tools" / "chat.jsonl"

CHANNEL = "sgcapital"
PREVIEW_URL = f"https://t.me/s/{CHANNEL}"
USER_AGENT = (
    "Mozilla/5.0 (compatible; fin-capital-2026-fetcher/1.0; "
    "+https://github.com/alexam247/fin_capital_2026)"
)

VISION_MODEL = "claude-haiku-4-5-20251001"
VISION_PROMPT = (
    "Ниже изображение из поста финансового Telegram-канала «Капитал» "
    "(инвестиционная аналитика, графики, таблицы). "
    "Опиши его одним-двумя короткими предложениями на русском. "
    "Без предисловий и общих фраз. "
    "Фокус: что показывает (тикер/ось/период) и главный визуальный вывод. "
    "Если это обложка/фото/мем, а не график — кратко опиши сюжет."
)


# ---------------------------------------------------------------------------
# HTML parsing
# ---------------------------------------------------------------------------


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_posts(html_text: str) -> list[dict]:
    """Extract posts from a t.me/s/<channel> preview HTML page.

    We find every `data-post="<channel>/<N>"` anchor and slice the HTML
    between consecutive anchors. Each slice is then scanned for the
    well-known Telegram widget fields with forgiving regexes.
    """
    matches = list(re.finditer(r'data-post="[^/]+/(\d+)"', html_text))
    posts: list[dict] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html_text)
        chunk = html_text[start:end]
        tg_id = int(m.group(1))

        # Text.
        text = ""
        mt = re.search(
            r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>\s*(?:<div|<a|$)',
            chunk,
            re.DOTALL,
        )
        if mt:
            raw = mt.group(1)
            raw = re.sub(r"<br\s*/?>", "\n", raw)
            raw = re.sub(r"</p>\s*<p[^>]*>", "\n\n", raw)
            raw = re.sub(r"<[^>]+>", "", raw)
            text = html_lib.unescape(raw).strip()

        # ISO datetime.
        date, time = "", ""
        md = re.search(r'<time[^>]*datetime="([^"]+)"', chunk)
        if md:
            iso = md.group(1)
            date = iso[:10]
            time = iso[11:19] if len(iso) >= 19 else ""

        # Images — background-image:url('...').
        image_urls = re.findall(r"background-image:url\('([^']+)'\)", chunk)
        image_urls = [u for u in image_urls if u.startswith("http")]

        # Forwarded-from label (optional).
        forwarded = None
        mf = re.search(
            r'tgme_widget_message_forwarded_from_name[^>]*>([^<]+)<', chunk
        )
        if mf:
            forwarded = html_lib.unescape(mf.group(1)).strip()

        posts.append(
            {
                "tg_id": tg_id,
                "date": date,
                "time": time,
                "text": text,
                "image_urls": image_urls,
                "forwarded_from": forwarded,
            }
        )
    return posts


# ---------------------------------------------------------------------------
# Vision analysis
# ---------------------------------------------------------------------------


def analyze_image(url: str, api_key: str) -> str:
    """Return a short Russian description of the image at `url`."""
    try:
        import anthropic  # type: ignore
    except ImportError:
        return f"[анализ недоступен: пакет anthropic не установлен] {url}"

    client = anthropic.Anthropic(api_key=api_key)
    try:
        resp = client.messages.create(
            model=VISION_MODEL,
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "url", "url": url},
                        },
                        {"type": "text", "text": VISION_PROMPT},
                    ],
                }
            ],
        )
    except Exception as e:  # noqa: BLE001 — log and move on
        return f"[анализ не удался: {e}] {url}"

    parts = [b.text for b in resp.content if getattr(b, "type", "") == "text"]
    desc = " ".join(parts).strip()
    return desc or f"[пустой ответ модели] {url}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def load_corpus() -> list[dict]:
    if not CORPUS.exists():
        return []
    return [
        json.loads(line)
        for line in CORPUS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="stop after N new posts")
    ap.add_argument(
        "--before",
        type=int,
        default=0,
        help="paginate backwards from the given Telegram post id",
    )
    args = ap.parse_args()

    existing = load_corpus()
    max_int_id = max((r["id"] for r in existing), default=0)
    max_date = max((r["date"] for r in existing), default="")
    tg_ids_seen = {
        int(r["msg_id"][3:])
        for r in existing
        if isinstance(r.get("msg_id"), str) and r["msg_id"].startswith("tg:")
    }
    max_tg_id = max(tg_ids_seen, default=0)
    first_run = not tg_ids_seen

    print(
        f"corpus: {len(existing)} rows, max_int_id={max_int_id}, "
        f"max_date={max_date}, max_tg_id={max_tg_id}, first_run={first_run}",
        file=sys.stderr,
    )

    url = PREVIEW_URL + (f"?before={args.before}" if args.before else "")
    try:
        html_text = fetch_html(url)
    except Exception as e:  # noqa: BLE001
        print(f"FETCH ERROR: {e}", file=sys.stderr)
        return 1

    posts = parse_posts(html_text)
    print(f"scraped {len(posts)} posts from {url}", file=sys.stderr)

    # Filter to new. On the very first run (no tg-sourced rows yet) we accept
    # only posts dated strictly after the latest date already in the corpus,
    # to avoid double-counting overlap with the HTML export.
    new_posts = []
    for p in sorted(posts, key=lambda x: x["tg_id"]):
        if p["tg_id"] in tg_ids_seen:
            continue
        if first_run and p["date"] and max_date and p["date"] <= max_date:
            continue
        if not p["text"] and not p["image_urls"]:
            continue
        new_posts.append(p)
        if args.limit and len(new_posts) >= args.limit:
            break

    if not new_posts:
        print("no new posts to append", file=sys.stderr)
        return 0

    # Vision pass.
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if api_key and not args.dry_run:
        print(
            f"analyzing images with {VISION_MODEL} "
            f"(ANTHROPIC_API_KEY present)",
            file=sys.stderr,
        )
    elif args.dry_run:
        print("dry-run: skipping image analysis", file=sys.stderr)
    else:
        print(
            "ANTHROPIC_API_KEY not set — images will be stored as URLs only",
            file=sys.stderr,
        )

    for p in new_posts:
        pieces = []
        for img_url in p["image_urls"]:
            if api_key and not args.dry_run:
                desc = analyze_image(img_url, api_key)
                pieces.append(f"[изображение] {desc}")
            else:
                pieces.append(f"[изображение] {img_url}")
        p["media_description"] = "\n".join(pieces) if pieces else None

    # Build rows.
    rows = []
    next_id = max_int_id
    for p in new_posts:
        next_id += 1
        rows.append(
            {
                "id": next_id,
                "date": p["date"],
                "time": p["time"],
                "author": "Капитал",
                "forwarded_from": p.get("forwarded_from"),
                "text": p["text"],
                "media": None,
                "media_description": p.get("media_description"),
                "source": "t.me/s/sgcapital",
                "msg_id": f"tg:{p['tg_id']}",
            }
        )

    if args.dry_run:
        print(f"DRY RUN: would append {len(rows)} rows:", file=sys.stderr)
        for r in rows:
            hl = (r["text"] or "").split("\n", 1)[0][:100]
            print(f"  + {r['date']} {r['msg_id']} — {hl}")
        return 0

    with CORPUS.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(
        f"appended {len(rows)} rows to {CORPUS.relative_to(ROOT)} "
        f"(new ids {max_int_id + 1}..{next_id})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
