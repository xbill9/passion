---
title: "GRIND404: I turned my hatred of LeetCode into a playable arcade game"
published: false
description: "A satirical arcade that scrapes real LeetCode problems, subverts them into parody with Gemini, and feeds your answers to a judge that was rigged against you from the start."
tags: weekendchallenge, googleai, showdev, webdev
cover_image: "https://raw.githubusercontent.com/xbill9/passion/main/docs/gameplay.gif"
---

*This is a submission for the [DEV Weekend Challenge: Passion Edition](https://dev.to/challenges/weekend-2026-07-09).*

## What I Built

My passion is not a hobby. It is not a sports team. It is a deep, principled, load-bearing **hatred of LeetCode** and the interview-industrial complex it represents.

The challenge asked for rivalry, fandom, and devotion. So I present devotion in its purest *negative* form:

## 💀 GRIND404 — the LeetCode Subversion Arcade

GRIND404 scrapes **real, live LeetCode problems**, **subverts** them into parody, and dares you to answer. But there's a twist that is also the entire point:

> You don't *solve* the problems. You *desecrate* them. A rigged judge rejects you no matter what — and **solving one honestly is a scoring penalty.**

You rack up points by being maximally cursed: `return true;`, hardcoding the test cases, DOSing the judge with `while(true){}`, negotiating the time complexity down to `O(vibes)`. The judge rejects all of it with escalating, passive-aggressive verdicts — and occasionally "accepts" your garbage just to hurt you.

![GRIND404 gameplay](https://raw.githubusercontent.com/xbill9/passion/main/docs/gameplay.gif)

## The Inspiration

Every developer has stared at a "Medium" problem with a 31% acceptance rate at 2am and felt something break. LeetCode turned the joy of programming into a grindable, gatekept, dopamine-slot-machine of a ritual that has almost nothing to do with the actual job.

I couldn't fix that in a weekend. But I could **make fun of it** in a weekend, and give everyone who's ever rage-quit a `Two Sum` variant a place to channel it. Catharsis-as-a-service.

## How It Works

```
 LeetCode GraphQL ──▶ Subversion Engine ──▶ Rigged Judge ──▶ Wall of Rejection
 (the live "mark")     Gemini / offline       never lets       (leaderboard)
                       template satire         you win
```

1. **Scrape the mark.** A FastAPI backend pulls a random real problem from LeetCode's public GraphQL endpoint. It's only ever used as *input* — the game never republishes LeetCode's copyrighted text. No network? It falls back to a shipped, self-authored problem set, so the whole thing runs air-gapped.
2. **Subvert it.** The problem is transformed into an honest, absurdist restatement plus a menu of gloriously degenerate answers.
3. **Judge it.** A rigged judge rejects everything and rewards degeneracy with points.
4. **Fail publicly.** Post your rank to the **Wall of Glorious Rejection**.

Here's a subverted round and one of the judge's verdicts:

![A subverted problem](https://raw.githubusercontent.com/xbill9/passion/main/docs/02-problem.png)
![The rigged judge rejects you anyway](https://raw.githubusercontent.com/xbill9/passion/main/docs/03-verdict.png)

## 🤖 Best Use of Google AI

The subversion engine is powered by **Google Gemini** (`gemini-2.5-flash`). Each round, Gemini is prompted — with a tuned system prompt and a few-shot example — to:

- rewrite the real problem as biting parody that references its actual mechanic (the sliding window, the DP table, the linked list),
- generate four "answers," three degenerate and exactly **one** honest-but-penalized trap,
- and write a rigged one-line verdict roasting both the answer *and* the industry.

Crucially, Gemini makes the game **sharper and endlessly varied** — but it is never a single point of failure. If there's no API key or the quota's dry, a deterministic template-satire engine takes over, so the demo *never* breaks. AI as an enhancement, not a dependency.

## Tech Stack

- **Backend:** FastAPI + httpx (async LeetCode + Gemini calls), Python 3.12
- **AI:** Google Gemini via REST, with an offline fallback engine
- **Frontend:** vanilla HTML/CSS/JS, no build step (because webpack is also LeetCode's fault)
- **Ship:** one slim Docker image, healthcheck, named volume for the leaderboard — `docker compose up` and you're grinding

## Try It

```bash
git clone https://github.com/xbill9/passion && cd passion
docker compose up --build          # offline satire, zero keys
# or, with AI subversion:
GEMINI_API_KEY=your_key docker compose up --build
# → http://localhost:8000
```

## A Good-Faith Note

Scraping LeetCode wholesale violates their ToS and their problem text is copyrighted. GRIND404 does **not** redistribute that content — it fetches a problem, transforms it into original parody/commentary, and only ever displays the subverted result. Live fetching is off-by-a-flag and a self-authored offline set ships in the box, so the app never *depends* on scraping. This is satire and commentary, made with love and spite in equal measure. Not affiliated with, endorsed by, or liked by LeetCode.

---

Built in a weekend out of pure spite. If you've ever been rejected for "insufficient passion," this one's for you. `#weekendchallenge`
