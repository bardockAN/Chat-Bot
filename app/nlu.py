from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional


# Very small rule-based NLU for Vietnamese


@dataclass
class Intent:
    name: str
    slots: Dict[str, str]


NORMALIZE_MAP = {
    "á": "a",
    "à": "a",
    "ả": "a",
    "ã": "a",
    "ạ": "a",
    "ă": "a",
    "ắ": "a",
    "ằ": "a",
    "ẳ": "a",
    "ẵ": "a",
    "ặ": "a",
    "â": "a",
    "ấ": "a",
    "ầ": "a",
    "ẩ": "a",
    "ẫ": "a",
    "ậ": "a",
    "đ": "d",
    "é": "e",
    "è": "e",
    "ẻ": "e",
    "ẽ": "e",
    "ẹ": "e",
    "ê": "e",
    "ế": "e",
    "ề": "e",
    "ể": "e",
    "ễ": "e",
    "ệ": "e",
    "í": "i",
    "ì": "i",
    "ỉ": "i",
    "ĩ": "i",
    "ị": "i",
    "ó": "o",
    "ò": "o",
    "ỏ": "o",
    "õ": "o",
    "ọ": "o",
    "ô": "o",
    "ố": "o",
    "ồ": "o",
    "ổ": "o",
    "ỗ": "o",
    "ộ": "o",
    "ơ": "o",
    "ớ": "o",
    "ờ": "o",
    "ở": "o",
    "ỡ": "o",
    "ợ": "o",
    "ú": "u",
    "ù": "u",
    "ủ": "u",
    "ũ": "u",
    "ụ": "u",
    "ư": "u",
    "ứ": "u",
    "ừ": "u",
    "ử": "u",
    "ữ": "u",
    "ự": "u",
    "ý": "y",
    "ỳ": "y",
    "ỷ": "y",
    "ỹ": "y",
    "ỵ": "y",
}


def normalize(text: str) -> str:
    text = text.lower()
    for src, dst in NORMALIZE_MAP.items():
        text = text.replace(src, dst)
    return text


def parse(text: str) -> Intent:
    t = normalize(text)
    raw = text.strip()

    # Order intent
    if any(k in t for k in ["dat sach", "mua sach", "mua cuon", "dat cuon", "dat ", "mua "]):
        slots: Dict[str, str] = {}
        # Try to capture title from RAW text (giữ dấu)
        m_raw = re.search(r"(?:mua|dat|đặt)(?:\s+sach|\s+cuon|\s+sách|\s+cuốn)?\s+(?P<title>.+)", raw, flags=re.IGNORECASE)
        if m_raw:
            title_raw = m_raw.group("title").strip()
            # Remove trailing quantity like "2 quyen/cuon"
            title_raw = re.sub(r"\s+\d+\s*(quy?en|cuon|cuốn)?\s*$", "", title_raw, flags=re.IGNORECASE)
            slots["title"] = title_raw
        # Quantity from normalized text
        q = re.search(r"(\d+)(?:\s*quy?en|\s*cuon|\s*cuon|\s*quy?n?)", t)
        if q:
            slots["quantity"] = q.group(1)
        return Intent(name="order", slots=slots)

    # Search by author
    m = re.search(r"tac gia\s+(?P<author>.+)", t)
    if m:
        return Intent(name="search_author", slots={"author": m.group("author").strip()})

    # Search by category
    m = re.search(r"the loai\s+(?P<category>.+)", t)
    if m:
        return Intent(name="search_category", slots={"category": m.group("category").strip()})

    # Stock/price for title
    m = re.search(r"(sach|cuon)?\s*(?P<title>.+?)\s*(con hang|gia|bao nhieu|con khong)$", t)
    if m:
        return Intent(name="search_title", slots={"title": m.group("title").strip()})

    # Generic search: contains "tim" or "co sach"
    if "tim" in t or "co sach" in t:
        m = re.search(r"tim\s+(?P<title>.+)", t)
        if m:
            return Intent(name="search_title", slots={"title": m.group("title").strip()})

    return Intent(name="chitchat", slots={})


