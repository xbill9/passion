# CLAUDE.md

Guidance for Claude Code (and humans) working in this repo.

## What this is

**GRIND404** — a satirical arcade game about hating LeetCode. It fetches real,
live LeetCode problems, **subverts** them into parody, and feeds player answers
to a *rigged* online judge that rejects everything and punishes honest, correct
solutions with negative points. The joke is the product; every mechanic
reinforces "the grind is rigged." See `PROJECT-GOALS.md` and `README.md` for the
full pitch.

Two design invariants worth keeping in mind before changing behavior:

- **Always playable.** No API key, no network → the game must still run. Live
  fetch and Gemini are *additive* flavors, never dependencies. Degrade
  gracefully; never crash on a timeout, a bad model response, or an unwritable
  leaderboard.
- **Never republish LeetCode content verbatim.** Fetched problem text is *only*
  ever input to the parody transform. The player only sees subverted output.

## Stack

- **Backend:** Python 3.12, FastAPI + Uvicorn, httpx for async calls. Source in `app/`.
- **Frontend:** vanilla HTML/CSS/JS, no build step. In `static/`.
- **AI (optional):** Google Gemini via REST (`gemini-2.5-flash`).
- **Deploy:** Docker + docker-compose.

## Common commands

Use the Makefile (`make help` lists everything):

```bash
make install     # create .venv and install deps
make dev         # run with autoreload → http://127.0.0.1:8000
make run         # run without autoreload
make up          # docker compose up --build (offline satire, no keys)
make down        # docker compose down
make clean       # remove caches + local leaderboard
```

There is **no test suite** yet. Verify changes by running the app (`make dev`)
and exercising the endpoints / UI in a browser.

## Architecture

Request flow for a round: `GET /api/round` → `leetcode.get_problem()` pulls a
problem (live or offline) → `subvert.subvert()` turns it into a parody prompt +
4 cursed choices → the round is cached server-side by `round_id` (point values
are **not** sent to the client). `POST /api/submit` looks up the round, scores
the choice or freeform answer, and `judge.verdict()` decides the rigged outcome.

- **`app/main.py`** — FastAPI app, all HTTP endpoints, in-memory round store
  (`_ROUNDS`, pruned), and the JSON-file leaderboard. Static frontend is mounted
  last at `/` so `/api/*` and `/health` win.
- **`app/leetcode.py`** — fetches a live problem from LeetCode's public GraphQL
  endpoint; strips HTML; falls back to `app/data/problems.json` when live is
  off/unavailable. Toggle with `LEETCODE_LIVE`.
- **`app/subvert.py`** — the Subversion Engine. Tries Gemini first (when
  `GEMINI_API_KEY` is set), falls back to a deterministic template engine
  (`_rule_based`) seeded per-problem via a tiny xorshift RNG so a given problem
  always subverts the same way. Also `score_freeform()` for hand-written answers.
- **`app/judge.py`** — the rigged judge. Rejects almost everything; rarely
  "ACCEPTS" high-scoring (≥120) cursed answers to hurt you. Verdict flavor and
  ranks come from `app/data/verdicts.json`.
- **`app/data/`** — `problems.json` (offline problem set), `verdicts.json`
  (rejection lines, rare accepts, rage lines, ranks). `leaderboard.json` is
  runtime-generated and gitignored.

## Conventions

- Determinism matters: `subvert` and `judge` avoid `random`/`Date` global state
  where a stable result is expected — `verdict()` takes a caller-supplied `roll`,
  and the rule-based engine seeds from the problem. Keep it that way.
- Failure paths swallow exceptions and fall back rather than raise (see the
  `try/except` in `leetcode`, `subvert`, and `_save_lb`). Preserve that "the game
  never crashes" posture when editing these paths.
- The "solve it honestly = negative points" trap must always be present on the
  choice menu (guaranteed in `_rule_based`; enforced by prompt for Gemini).

## Configuration (env vars)

| Var | Default | Purpose |
|-----|---------|---------|
| `GEMINI_API_KEY` | *(empty)* | Enables Gemini subversion; empty → offline template satire |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model to call |
| `LEETCODE_LIVE` | `1` | `0` forces the shipped offline problem set |
| `ROUNDS_PER_GAME` | `10` | Rounds per run |
| `LEADERBOARD_PATH` | `app/data/leaderboard.json` | Where the leaderboard persists |
