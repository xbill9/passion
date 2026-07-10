"""The Rigged Judge. It never really wanted you to win."""
from __future__ import annotations

import json
from pathlib import Path

_V = json.loads((Path(__file__).parent / "data" / "verdicts.json").read_text())


def verdict(points: int, roll: int) -> dict:
    """Return a status + flavor. Cursed answers score high but 'lose'; that's
    the joke — the judge rejects everything, occasionally 'accepts' to hurt you.
    `roll` is a caller-supplied non-negative int so we stay deterministic."""
    accepted = points >= 120 and roll % 5 == 0
    if accepted:
        bank = _V["rare_accepts"]
        status = "ACCEPTED"
    else:
        bank = _V["rejections"]
        status = "REJECTED"
    return {
        "status": status,
        "message": bank[roll % len(bank)],
        "rage_line": _V["rage_lines"][roll % len(_V["rage_lines"])],
    }


def rank_for(score: int) -> dict:
    for r in _V["ranks"]:
        if score >= r["min"]:
            return {"title": r["title"], "line": r["line"]}
    last = _V["ranks"][-1]
    return {"title": last["title"], "line": last["line"]}
