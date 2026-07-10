# GRIND404 — Project Goals

> *A game about hating LeetCode.*

## The Passion

This project is built on one honest, load-bearing emotion: **a deep, principled
hatred of LeetCode** and the tech-interview-industrial complex it represents.
The DEV "Passion" weekend challenge asked for rivalry, fandom, and devotion —
so this is devotion in its purest negative form. We are fans of the grind the
way you're a fan of a splinter.

GRIND404 turns that resentment into a playable joke: a satirical arcade that
takes real LeetCode problems and **subverts them into parody**, then feeds your
answers to a judge that was rigged against you from the start.

## Core Idea

1. **Pull a real "mark."** The app fetches a live problem from LeetCode's public
   GraphQL endpoint (`app/leetcode.py`).
2. **Subvert it.** The problem is never shown verbatim. It's transformed into an
   absurdist parody restatement plus a menu of gloriously cursed "answers"
   (`app/subvert.py`).
3. **Judge it dishonestly.** A rigged judge (`app/judge.py`) rejects nearly
   everything, occasionally "ACCEPTS" just to hurt you, and — the central joke —
   **punishes honest, correct, optimal solutions with negative points.**
4. **Climb the wall of rejection.** Points, rage meter, ranks, and a persistent
   leaderboard reward maximum degeneracy over actual competence.

## What "Subvert the live problems" Means (and its limits)

The satire only works if it's aimed at real targets, so we ingest live LeetCode
content — but we do it defensibly:

- **Never republish.** LeetCode's problem text is copyrighted and their ToS
  forbids wholesale scraping. GRIND404 uses the fetched text *only as input* to a
  parody/commentary transform. The verbatim content never reaches the player —
  what they see is transformative satire (defensible as commentary/parody).
- **Punch up, never down.** The comedy targets gatekeeping interview culture and
  the platform, never individual people.
- **Air-gapped by default.** If the network is gone, LeetCode blocks us, or their
  schema shifts, the game falls back to a shipped set of self-authored problem
  blurbs (`app/data/problems.json`) so the container always plays. Set
  `LEETCODE_LIVE=0` to force fully offline mode.

## The Subversion Engine

Two interchangeable backends, so the game is funny with or without an API key:

- **Google Gemini (optional).** With `GEMINI_API_KEY` set, Gemini rewrites each
  problem into fresh biting parody — this is the "Best Use of Google AI" angle.
- **Rule-based fallback (always on).** A deterministic, keyless, offline template
  engine guarantees the container runs self-contained with zero external
  dependencies or secrets.

## Containerization Goals

Fully self-contained and portable — "clone and `docker compose up`":

- **`Dockerfile`** — slim Python 3.12 image, health-checked, single process.
- **`docker-compose.yml`** — one service (`grind404`), a persistent volume for the
  leaderboard, and env toggles for AI/live/offline behavior.
- **No required secrets.** Runs air-gapped out of the box; keys only *add* the
  live-fetch and Gemini flavors.

## Tech Stack

| Layer      | Choice                                             |
|------------|----------------------------------------------------|
| Backend    | Python + FastAPI + Uvicorn (`app/`)                |
| Frontend   | Static HTML/CSS/JS arcade (`static/`)              |
| AI (opt.)  | Google Gemini via REST (`gemini-2.5-flash`)        |
| Ingest     | LeetCode public GraphQL, with offline cache        |
| Deploy     | Docker + docker-compose                            |

## Design Principles

- **The joke is the product.** Every mechanic reinforces "the grind is rigged."
- **Always playable.** No key, no network, no problem — it degrades gracefully.
- **Legally defensible satire.** Transform, never republish; punch up.
- **Zero-crash humor.** A leaderboard that can't persist, a model that times out,
  or an expired round should never take down the game.

## Success Criteria

- Runs with a single `docker compose up`, offline, no config.
- Every round feels like a fresh, funny attack on interview culture.
- Nothing copyrighted is ever shown verbatim.
- It makes at least one exhausted engineer laugh instead of cry.

---

*Built for the DEV Community "Build Something Inspired by Passion" weekend
challenge. See `challenge-summary.md` for rules, dates, and prize categories.*
