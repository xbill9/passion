"""Fetch real LeetCode problems (the marks) to be subverted.

We hit LeetCode's public GraphQL endpoint to pull a live problem, then hand the
raw text to the subversion engine. We NEVER display LeetCode's content verbatim
in the game — it is only ever an input to a parody transform. If the network is
gone, LeetCode blocks us, or their schema shifts, we fall back to a shipped set
of self-authored blurbs so the container always plays.
"""
from __future__ import annotations

import json
import os
import random
import re
from pathlib import Path

import httpx

_DATA = Path(__file__).parent / "data"
_OFFLINE: list[dict] = json.loads((_DATA / "problems.json").read_text())

GRAPHQL_URL = "https://leetcode.com/graphql"
LIVE_ENABLED = os.getenv("LEETCODE_LIVE", "1") != "0"
_TIMEOUT = float(os.getenv("LEETCODE_TIMEOUT", "6"))

_QUERY = """
query subvertTarget($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionId
    title
    titleSlug
    difficulty
    content
  }
}
"""

_HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com",
    "User-Agent": "Mozilla/5.0 (compatible; GRIND404/1.0; satire)",
}


def _strip_html(html: str) -> str:
    """Crudely flatten LeetCode's HTML/entities into plain text."""
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"),
                 ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'")):
        text = text.replace(a, b)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:1200]


async def _fetch_live(slug: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, headers=_HEADERS) as client:
            resp = await client.post(
                GRAPHQL_URL,
                json={"query": _QUERY, "variables": {"titleSlug": slug}},
            )
        resp.raise_for_status()
        q = (resp.json().get("data") or {}).get("question")
        if not q or not q.get("content"):
            return None
        return {
            "slug": q["titleSlug"],
            "title": q["title"],
            "difficulty": q.get("difficulty", "Unknown"),
            "blurb": _strip_html(q["content"]),
            "source": "live",
        }
    except Exception:
        return None


async def get_problem() -> dict:
    """Return one problem to subvert, preferring a live LeetCode pull."""
    picked = random.choice(_OFFLINE)
    if LIVE_ENABLED:
        live = await _fetch_live(picked["slug"])
        if live:
            return live
    return {**picked, "source": "offline"}
