# GRIND404 💀 — the LeetCode Subversion Arcade

> Built for the DEV **Weekend Challenge: Passion Edition**. My passion is a
> pure, load-bearing hatred of LeetCode. So I made a game about it.

GRIND404 scrapes **real, live LeetCode problems** and **subverts** them into
parody. You don't *solve* them — you *desecrate* them. A rigged online judge
rejects you no matter what, occasionally "accepting" your code just to hurt you.
Score points by being maximally cursed (`return true;`, hardcoding test cases,
DOSing the judge). Solving a problem honestly is a **penalty**. That's the joke.
That's the catharsis.

![vibe](https://img.shields.io/badge/status-rejected-ef4743) ![vibe](https://img.shields.io/badge/passion-hatred-ffa116)

---

## How it works

```
 LeetCode GraphQL ──▶ Subversion Engine ──▶ Rigged Judge ──▶ Wall of Rejection
 (the live "mark")     Gemini or offline      never lets        (leaderboard)
                       template satire        you win
```

1. **Scrape.** The backend pulls a random real problem from LeetCode's public
   GraphQL endpoint (`app/leetcode.py`). It's only ever used as *input* — the
   game never displays LeetCode's copyrighted text verbatim (see *Legal* below).
   No network? It falls back to a shipped, self-authored problem set.
2. **Subvert.** The problem is mutated into an honest, absurdist restatement plus
   a menu of gloriously cursed "answers" (`app/subvert.py`). Uses **Google Gemini**
   when `GEMINI_API_KEY` is set; otherwise a deterministic template-satire engine
   so the container works with zero keys and zero network.
3. **Judge.** The rigged judge (`app/judge.py`) rejects everything with escalating
   absurdity, and rewards degeneracy with points.
4. **Fail publicly.** Post your rejection to the leaderboard — the Wall of
   Glorious Rejection.

## Run it

### Docker (recommended — it's the whole point)

```bash
# Fully offline satire, no keys needed:
docker compose up --build
# → http://localhost:8000

# With AI subversion (targets the "Best Use of Google AI" prize):
GEMINI_API_KEY=your_key docker compose up --build
```

### Plain Docker

```bash
docker build -t grind404 .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key grind404
```

### Local (no Docker)

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000
```

## Configuration

| Env var            | Default            | What it does |
|--------------------|--------------------|--------------|
| `GEMINI_API_KEY`   | *(empty)*          | Enables Gemini-powered subversion. Empty → offline template satire. |
| `GEMINI_MODEL`     | `gemini-2.5-flash` | Which Gemini model to call. |
| `LEETCODE_LIVE`    | `1`                | `0` forces the shipped offline problem set (air-gapped). |
| `ROUNDS_PER_GAME`  | `10`               | Injustices per run. |
| `LEADERBOARD_PATH` | `app/data/leaderboard.json` | Where the wall persists. |

## The "Best Use of Google AI" angle

When `GEMINI_API_KEY` is set, every round's parody rewrite and its menu of cursed
answers are generated live by Gemini, prompted to punch up at interview-grind
culture and to always plant exactly one "solve it honestly (penalty)" trap. The
offline fallback means the demo never breaks if a key/quota isn't handy — Gemini
makes it *sharper and endlessly varied*, it isn't a single point of failure.

## Tech

- **Backend:** FastAPI + httpx (async LeetCode + Gemini calls), Python 3.12
- **Frontend:** vanilla HTML/CSS/JS, no build step (because webpack is also
  LeetCode's fault)
- **Container:** single slim image, healthcheck, named volume for the leaderboard

## Legal / good-faith note

Scraping LeetCode wholesale violates their ToS and their problem text is
copyrighted. GRIND404 does **not** republish that content: it fetches a problem,
transforms it into original parody/commentary, and only ever shows the subverted
result — a use that leans on satire and commentary rather than redistribution.
Live fetching is off-by-a-flag (`LEETCODE_LIVE=0`) and the app ships a fully
self-authored offline problem set so it never *depends* on scraping. Not
affiliated with, endorsed by, or liked by LeetCode.

---

*Made in a weekend out of pure spite.* `#weekendchallenge`
