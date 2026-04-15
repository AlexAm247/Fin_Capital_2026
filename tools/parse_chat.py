#!/usr/bin/env python3
"""Parse Telegram HTML export (messages*.html) into a clean JSONL corpus.

Output: tools/chat.jsonl with one record per message:
    {"id": int, "date": "YYYY-MM-DD", "time": "HH:MM:SS",
     "author": str, "text": str, "source": "messages.html", "msg_id": "messageN"}
Service messages (date dividers, "channel created", etc.) are skipped.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
FILES = ["messages.html", "messages2.html", "messages3.html"]
OUT = ROOT / "tools" / "chat.jsonl"

TITLE_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}:\d{2}:\d{2})")


def text_with_breaks(node) -> str:
    """Return inner text, turning <br> into newlines and collapsing whitespace."""
    # Replace <br> with \n
    for br in node.find_all("br"):
        br.replace_with("\n")
    txt = node.get_text()
    # Normalize whitespace but keep newlines
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in txt.splitlines()]
    return "\n".join(ln for ln in lines if ln is not None).strip()


def parse_file(path: Path, counter: list[int]) -> list[dict]:
    soup = BeautifulSoup(path.read_bytes(), "lxml")
    out: list[dict] = []
    last_author = None
    for msg in soup.select("div.message.default"):
        body = msg.find("div", class_="body")
        if not body:
            continue
        date_div = body.find("div", class_="date")
        if not date_div:
            continue
        title = date_div.get("title", "")
        m = TITLE_RE.search(title)
        if not m:
            continue
        dd, mm, yyyy, hms = m.groups()
        date = f"{yyyy}-{mm}-{dd}"

        # from_name (may be absent in joined messages — inherit last)
        fn_div = body.find("div", class_="from_name")
        if fn_div:
            last_author = fn_div.get_text(strip=True)
        author = last_author or ""

        # Forwarded-from marker
        fwd_div = body.find("div", class_="forwarded")
        forwarded_from = None
        if fwd_div:
            ffn = fwd_div.find("div", class_="from_name")
            if ffn:
                forwarded_from = ffn.get_text(strip=True)

        text_div = body.find("div", class_="text")
        text = text_with_breaks(text_div) if text_div else ""

        # Media description (photo caption is inside text_div; for pure media w/o
        # caption we capture the media title so the index isn't blind to it)
        media_div = body.find("div", class_="media_wrap")
        media = None
        if media_div:
            title_el = media_div.find("div", class_="title")
            desc_el = media_div.find("div", class_="description")
            parts = []
            if title_el:
                parts.append(title_el.get_text(strip=True))
            if desc_el:
                parts.append(desc_el.get_text(strip=True))
            if parts:
                media = " — ".join(parts)

        if not text and not media:
            continue

        counter[0] += 1
        out.append(
            {
                "id": counter[0],
                "date": date,
                "time": hms,
                "author": author,
                "forwarded_from": forwarded_from,
                "text": text,
                "media": media,
                "source": path.name,
                "msg_id": msg.get("id", ""),
            }
        )
    return out


def main() -> None:
    counter = [0]
    all_msgs: list[dict] = []
    for name in FILES:
        path = ROOT / name
        if not path.exists():
            print(f"skip missing {name}")
            continue
        msgs = parse_file(path, counter)
        print(f"{name}: {len(msgs)} messages")
        all_msgs.extend(msgs)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for rec in all_msgs:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"total: {len(all_msgs)} -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
