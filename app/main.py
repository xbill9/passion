"""GRIND404 — FastAPI backend for the LeetCode Subversion Arcade."""
from __future__ import annotations

import json
import os
import random
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import judge, leetcode, subvert

ROOT = Path(__file__).parent.parent
STATIC = ROOT / "static"
LB_PATH = Path(os.getenv("LEADERBOARD_PATH", ROOT / "app" / "data" / "leaderboard.json"))
ROUNDS_PER_GAME = int(os.getenv("ROUNDS_PER_GAME", "10"))

app = FastAPI(title="GRIND404", description="A game about hating LeetCode.")

# round_id -> {choices, expires}. Ephemeral; fine for a party game.
_ROUNDS: dict[str, dict] = {}
_MAX_ROUNDS = 5000


def _prune() -> None:
    if len(_ROUNDS) <= _MAX_ROUNDS:
        return
    now = time.time()
    stale = [k for k, v in _ROUNDS.items() if v["expires"] < now]
    for k in stale:
        _ROUNDS.pop(k, None)
    # If still huge (many concurrent players), drop oldest arbitrarily.
    while len(_ROUNDS) > _MAX_ROUNDS:
        _ROUNDS.pop(next(iter(_ROUNDS)), None)


def _load_lb() -> list[dict]:
    try:
        return json.loads(LB_PATH.read_text())
    except Exception:
        return []


def _save_lb(entries: list[dict]) -> None:
    try:
        LB_PATH.parent.mkdir(parents=True, exist_ok=True)
        LB_PATH.write_text(json.dumps(entries, indent=2))
    except Exception:
        pass  # a leaderboard that can't persist should never crash the game


@app.get("/api/config")
async def config() -> dict:
    return {
        "rounds": ROUNDS_PER_GAME,
        "gemini": bool(subvert.GEMINI_API_KEY),
        "live_leetcode": leetcode.LIVE_ENABLED,
    }


@app.get("/api/round")
async def new_round() -> dict:
    problem = await leetcode.get_problem()
    sub = await subvert.subvert(problem)

    round_id = uuid.uuid4().hex
    _ROUNDS[round_id] = {
        "choices": {c["id"]: c for c in sub["choices"]},
        "expires": time.time() + 3600,
    }
    _prune()

    # Do not leak point values to the client; the judge decides on submit.
    public_choices = [{"id": c["id"], "text": c["text"]} for c in sub["choices"]]
    return {
        "round_id": round_id,
        "title": sub["title"],
        "difficulty": sub["difficulty"],
        "prompt": sub["prompt"],
        "choices": public_choices,
        "source": problem.get("source", "offline"),
        "engine": sub["engine"],
    }


class Submission(BaseModel):
    round_id: str
    choice_id: int | None = None
    freeform: str | None = None


@app.post("/api/submit")
async def submit(sub: Submission) -> dict:
    rnd = _ROUNDS.get(sub.round_id)
    if not rnd:
        raise HTTPException(status_code=404, detail="Round expired or unknown. The grind stops for no one.")

    if sub.freeform and sub.freeform.strip():
        points, judge_line = subvert.score_freeform(sub.freeform.strip())
    elif sub.choice_id is not None and sub.choice_id in rnd["choices"]:
        choice = rnd["choices"][sub.choice_id]
        points, judge_line = choice["points"], choice["judge"]
    else:
        raise HTTPException(status_code=400, detail="Pick a cursed answer or write your own.")

    roll = random.randint(0, 10_000)
    v = judge.verdict(points, roll)
    rage = max(0, min(20, points // 8)) + (8 if v["status"] == "ACCEPTED" else 0)

    # One-shot per round.
    _ROUNDS.pop(sub.round_id, None)

    return {
        "points": points,
        "rage": rage,
        "status": v["status"],
        "message": v["message"],
        "roast": judge_line,
        "rage_line": v["rage_line"],
    }


class ScoreEntry(BaseModel):
    name: str
    score: int


@app.get("/api/leaderboard")
async def leaderboard() -> dict:
    entries = sorted(_load_lb(), key=lambda e: e["score"], reverse=True)[:15]
    return {"entries": entries}


@app.post("/api/leaderboard")
async def add_score(entry: ScoreEntry) -> dict:
    name = (entry.name or "anon").strip()[:20] or "anon"
    score = int(entry.score)
    entries = _load_lb()
    entries.append({"name": name, "score": score, "rank": judge.rank_for(score)["title"]})
    entries = sorted(entries, key=lambda e: e["score"], reverse=True)[:100]
    _save_lb(entries)
    top = entries[:15]
    placed = next((i + 1 for i, e in enumerate(top)
                   if e["name"] == name and e["score"] == score), None)
    return {"entries": top, "placed": placed, "rank": judge.rank_for(score)}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


# Static frontend (mounted last so /api/* and /health win).
app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
