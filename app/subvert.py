"""The Subversion Engine.

Takes a real LeetCode problem and mutates it into a parody: an honest,
absurdist restatement plus a menu of gloriously cursed "answers" the player
can submit. Uses Google Gemini when GEMINI_API_KEY is set (this is the
'Best Use of Google AI' angle), and falls back to a deterministic template
satire engine so the container is fully self-contained without any keys.
"""
from __future__ import annotations

import hashlib
import json
import os
import re

import httpx

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)
_TIMEOUT = float(os.getenv("GEMINI_TIMEOUT", "12"))

# ---------------------------------------------------------------------------
# Rule-based fallback (no network, no keys, always works)
# ---------------------------------------------------------------------------

_PROMPT_TEMPLATES = [
    'Given {title} and the crushing weight of the tech-interview industrial '
    "complex, return two indices that sum to your dwindling self-worth.",
    'Reframe "{title}" as a cry for help. You have 45 minutes and one (1) '
    "human being silently judging your variable names.",
    'Solve {title}, but remember: a stranger did it in four lines in 2014 and '
    "the interviewer has never emotionally recovered.",
    'The problem "{title}" is Easy. The problem "{title}" has a 31% acceptance '
    "rate. Both of these things are true and neither is your fault.",
    'Implement {title}. The optimal solution is obvious in hindsight, useless '
    "in foresight, and forgotten by lunch.",
    'Consider {title}. Now consider that no job you actually want will ever '
    "ask you to do this. Proceed anyway. Passionately.",
]

_CHOICES_BANK = [
    ("return true; // trust me", 120,
     "return true; on a problem that returns an integer. Bold. Rejected. Iconic."),
    ("Hardcode all the test cases in a giant switch", 150,
     "You memorized the judge instead of the algorithm. Deeply illegal. +respect."),
    ("while(true){} to DOS the judge", 140,
     "The judge's CPU is now warmer than your job prospects. TLE, but at what cost."),
    ("Copy the top-voted 'easy one-liner' with no idea how it works", 90,
     "Pasted a one-liner. It works. You will never know why. Neither will they."),
    ("Add // TODO: optimize and submit immediately", 70,
     "The TODO will outlive us all. Presentation Error."),
    ("Solve it correctly and optimally (nerd)", -15,
     "You actually solved it. Correctly. Efficiently. Rejected for insufficient passion."),
    ("Bribe the recruiter with a LinkedIn 'Congrats!'", 110,
     "The recruiter has circled back. It is a noose made of calendar invites."),
    ("Rename every variable to 'temp' and pray", 80,
     "temp, temp2, temp_final, temp_final_v2_USE_THIS. Chef's kiss. Wrong Answer."),
    ("Print the answer to stderr and act confused", 95,
     "Output Limit Exceeded: too much cope in stderr."),
    ("Rage quit and open Twitter to post about the grind", 100,
     "Your thread got 3 likes. One was a bot. This is the real accepted answer."),
    ("Ask an AI, paste its answer, add a semicolon so it's 'yours'", 115,
     "The semicolon is the only line you wrote and it was optional. Rejected."),
    ("catch(Exception e){ return correctAnswer; }", 130,
     "You wrapped the whole problem in a try/catch of denial. Beautiful. Wrong."),
    ("Import a library that literally solves it, call it a day", 105,
     "import solve_the_problem. The maintainer is also unemployed. Solidarity."),
    ("Submit pseudocode and gesture vaguely at 'the idea'", 60,
     "'You can see where I'm going with this.' We could not. Compilation Error."),
    ("Negotiate the time complexity down to O(vibes)", 125,
     "O(vibes) is technically constant if you stop caring. TLE anyway."),
    ("Sacrifice your weekend, streak, and one (1) friendship", 85,
     "The owl accepted the sacrifice. The company did not. Classic trade."),
    ("Blame the problem statement for being 'ambiguous'", 75,
     "You're right, and it changes nothing. Wrong Answer, correctly diagnosed."),
    ("git commit -m 'fix' and force push over the correct solution", 135,
     "You force-pushed away the only working code. Menace behavior. +respect."),
]


def _seed(problem: dict) -> int:
    raw = f"{problem['slug']}::{problem['title']}".encode()
    return int(hashlib.sha256(raw).hexdigest(), 16)


def _rule_based(problem: dict) -> dict:
    seed = _seed(problem)
    rng = _StableRng(seed)
    title = problem["title"]
    prompt = rng.choice(_PROMPT_TEMPLATES).format(title=title)

    bank = list(_CHOICES_BANK)
    rng.shuffle(bank)
    picks = bank[:4]
    # Guarantee the "solve it honestly" trap is on the menu.
    honest = next(c for c in _CHOICES_BANK if c[1] < 0)
    if honest not in picks:
        picks[-1] = honest
    rng.shuffle(picks)

    choices = [
        {"id": i, "text": t, "points": p, "judge": j}
        for i, (t, p, j) in enumerate(picks)
    ]
    return {
        "title": title,
        "difficulty": problem.get("difficulty", "Unknown"),
        "prompt": prompt,
        "choices": choices,
        "engine": "rule-based",
    }


class _StableRng:
    """Tiny deterministic RNG so a given problem always subverts the same way
    (without importing random's global state or needing Date/seed hacks)."""

    def __init__(self, seed: int):
        self.state = seed & 0xFFFFFFFFFFFFFFFF

    def _next(self) -> int:
        # xorshift64
        x = self.state or 0x9E3779B97F4A7C15
        x ^= (x << 13) & 0xFFFFFFFFFFFFFFFF
        x ^= x >> 7
        x ^= (x << 17) & 0xFFFFFFFFFFFFFFFF
        self.state = x
        return x

    def choice(self, seq):
        return seq[self._next() % len(seq)]

    def shuffle(self, seq):
        for i in range(len(seq) - 1, 0, -1):
            j = self._next() % (i + 1)
            seq[i], seq[j] = seq[j], seq[i]


# ---------------------------------------------------------------------------
# Gemini path (Best Use of Google AI)
# ---------------------------------------------------------------------------

_SYSTEM = """You are the Subversion Engine for GRIND404, a satirical arcade that \
weaponizes a developer's hatred of LeetCode and tech-interview culture. Given a \
real coding problem, rewrite it as biting parody and produce a menu of gloriously \
degenerate "answers" a player submits to a rigged online judge that hates them.

VOICE: dry, deadpan, a little unhinged — think a burned-out senior engineer at \
2am. Specific and surprising, never generic. Land a real joke, not just \
"lol this is hard". Reference the actual problem's mechanic (the sliding window, \
the DP table, the linked list) so the parody bites. One or two sentences, max ~45 \
words for the prompt.

PUNCH UP at LeetCode, gatekeeping, grind culture, and clueless recruiters — never \
down at the player or any real, named person. PG-13: no slurs, no real names.

CHOICES — exactly 4, each a distinct flavor of cheating/coping:
- 3 of them are cursed/degenerate hacks (hardcoding, return true, DOSing the \
  judge, asking an AI, blaming the spec, force-pushing, O(vibes)). Points 60-160.
- EXACTLY ONE is "actually solve it correctly/optimally" and MUST have NEGATIVE \
  points (-30..-5). Punishing honest grinding is the entire joke; never omit it.
- "text" ≤ 90 chars, imperative and funny. "judge" ≤ 140 chars: a rigged verdict \
  that roasts the choice AND the industry.

Example for "Two Sum":
{"prompt":"Given the crushing weight of the tech-interview complex, return two \
indices summing to your dwindling self-worth. A HashMap will not fix your life, \
but it is O(n), so.","choices":[{"text":"return [0,1]; it's basically always [0,1]","points":120,"judge":"Statistically brave. Test 2/57 disagreed. Wrong Answer, gambler."},{"text":"Nested for-loops, O(n^2), embrace the shame","points":85,"judge":"Time Limit Exceeded — the judge watched, and it pitied you."},{"text":"Build the HashMap like a functioning adult","points":-20,"judge":"Correct and optimal. Rejected for insufficient passion. Try suffering more."},{"text":"Paste the discussion-tab one-liner, understand nothing","points":95,"judge":"It works. You will never know why. Neither will your future team."}]}

Respond with ONLY valid minified JSON, no markdown fences, matching:
{"prompt": str, "choices": [{"text": str, "points": int, "judge": str}]}"""


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no json object in model output")
    return json.loads(text[start:end + 1])


async def _gemini(problem: dict) -> dict | None:
    if not GEMINI_API_KEY:
        return None
    user = (
        f"Real problem title: {problem['title']}\n"
        f"Difficulty: {problem.get('difficulty', 'Unknown')}\n"
        f"Description (for context, do not copy verbatim):\n{problem.get('blurb', '')}\n\n"
        "Subvert it now."
    )
    payload = {
        "systemInstruction": {"parts": [{"text": _SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"temperature": 1.0, "responseMimeType": "application/json"},
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                _GEMINI_URL,
                params={"key": GEMINI_API_KEY},
                json=payload,
            )
        resp.raise_for_status()
        parts = resp.json()["candidates"][0]["content"]["parts"]
        raw = "".join(p.get("text", "") for p in parts)
        data = _extract_json(raw)

        choices_in = data["choices"][:4]
        if len(choices_in) < 4:
            return None
        choices = []
        for i, c in enumerate(choices_in):
            choices.append({
                "id": i,
                "text": str(c["text"])[:140],
                "points": int(c["points"]),
                "judge": str(c["judge"])[:200],
            })
        return {
            "title": problem["title"],
            "difficulty": problem.get("difficulty", "Unknown"),
            "prompt": str(data["prompt"])[:400],
            "choices": choices,
            "engine": f"gemini:{GEMINI_MODEL}",
        }
    except Exception:
        return None


async def subvert(problem: dict) -> dict:
    """Turn a real problem into a subverted round. Gemini first, rules fallback."""
    result = await _gemini(problem)
    if result:
        return result
    return _rule_based(problem)


def score_freeform(answer: str) -> tuple[int, str]:
    """Score a player's hand-crafted cursed answer by how degenerate it is."""
    a = answer.lower()
    score = 40
    hits = []
    signals = {
        "return true": (60, "return true; energy detected"),
        "return false": (45, "committed to the wrong boolean. respect"),
        "hardcode": (70, "hardcoding the test cases, a felony we admire"),
        "while(true": (65, "infinite loop deployed against the judge"),
        "while (true": (65, "infinite loop deployed against the judge"),
        "todo": (35, "a TODO that will outlive civilization"),
        "sleep": (55, "stalling the judge like a true professional"),
        "print": (30, "debugging via print like the ancients"),
        "chatgpt": (50, "outsourced to a chatbot, deeply on-brand"),
        "copilot": (50, "the copilot flew you straight into a mountain"),
        "sudo": (60, "sudo solve-my-problem, denied but noted"),
        "recursion": (25, "recursion, or as the judge calls it, a stack overflow speedrun"),
        "0xdead": (75, "hex-level menace"),
    }
    for key, (pts, msg) in signals.items():
        if key in a:
            score += pts
            hits.append(msg)
    if len(a) < 4:
        score += 25
        hits.append("brevity is the soul of getting rejected")
    judge = "; ".join(hits[:3]) or "the judge squinted and rejected it on general principle"
    return min(score, 200), judge.capitalize() + "."
