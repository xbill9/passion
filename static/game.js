// GRIND404 — client. Vanilla JS, no build step, because webpack is also LeetCode's fault.
"use strict";

const $ = (id) => document.getElementById(id);
const api = (path, opts) => fetch(path, opts).then((r) => {
  if (!r.ok) return r.json().then((e) => Promise.reject(e.detail || "the grind broke"));
  return r.json();
});

const state = { round: 0, total: 10, score: 0, rage: 0, current: null, busy: false };

function show(screenId) {
  document.querySelectorAll(".screen").forEach((s) => s.classList.remove("active"));
  $(screenId).classList.add("active");
}

// ---------- config / badges ----------
async function loadConfig() {
  try {
    const cfg = await api("/api/config");
    state.total = cfg.rounds;
    $("round-total").textContent = cfg.rounds;
    const eb = $("engine-badge");
    eb.textContent = "engine: " + (cfg.gemini ? "gemini ✨" : "offline satire");
    if (cfg.gemini) eb.classList.add("hot");
  } catch (_) { /* game still works with defaults */ }
}

// ---------- game flow ----------
function startGame() {
  state.round = 0; state.score = 0; state.rage = 0;
  $("score").textContent = "0";
  updateRage();
  show("screen-game");
  nextRound();
}

async function nextRound() {
  if (state.round >= state.total) return endGame();
  state.round++;
  $("round-num").textContent = state.round;
  $("verdict").classList.add("hidden");
  $("freeform").value = "";
  $("p-title").textContent = "Loading a fresh injustice…";
  $("p-prompt").textContent = "Subverting…";
  $("p-diff").textContent = "—";
  $("choices").innerHTML = "";
  state.busy = false;

  try {
    const r = await api("/api/round");
    state.current = r;
    $("p-title").textContent = "SUBVERTED: " + r.title;
    $("p-prompt").textContent = r.prompt;
    const diff = $("p-diff");
    diff.textContent = r.difficulty;
    diff.className = "diff " + r.difficulty;
    const sb = $("source-badge");
    sb.textContent = "source: " + (r.source === "live" ? "live leetcode 🔴" : "cached");
    sb.classList.toggle("hot", r.source === "live");

    const box = $("choices");
    box.innerHTML = "";
    r.choices.forEach((c) => {
      const b = document.createElement("button");
      b.className = "choice";
      b.textContent = c.text;
      b.onclick = () => submit({ round_id: r.round_id, choice_id: c.id });
      box.appendChild(b);
    });
  } catch (err) {
    $("p-prompt").textContent = "The judge's server also hates you (" + err + "). Retrying is futile but try anyway.";
  }
}

function submitFreeform() {
  const val = $("freeform").value.trim();
  if (!val || !state.current) return;
  submit({ round_id: state.current.round_id, freeform: val });
}

async function submit(payload) {
  if (state.busy) return;
  state.busy = true;
  document.querySelectorAll(".choice").forEach((b) => (b.disabled = true));
  try {
    const res = await api("/api/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    applyVerdict(res);
  } catch (err) {
    // Round likely expired — just move on; the grind waits for no one.
    state.busy = false;
    nextRound();
  }
}

function applyVerdict(res) {
  state.score += res.points;
  state.rage = Math.min(100, state.rage + res.rage);
  const scoreEl = $("score");
  scoreEl.textContent = state.score;
  scoreEl.classList.remove("bump"); void scoreEl.offsetWidth; scoreEl.classList.add("bump");
  updateRage();

  const stamp = $("verdict-stamp");
  const accepted = res.status === "ACCEPTED";
  stamp.textContent = res.status;
  stamp.className = "stamp" + (accepted ? " accepted" : "");
  $("verdict-msg").textContent = res.message;
  $("verdict-roast").textContent = "⚖ " + res.roast;
  $("verdict-rage").textContent = res.rage_line;
  $("verdict-points").textContent = res.points;
  $("verdict").classList.remove("hidden");
  const g = $("screen-game");
  g.classList.remove("shake"); void g.offsetWidth; g.classList.add("shake");
  $("verdict").scrollIntoView({ behavior: "smooth", block: "center" });
}

function updateRage() {
  $("rage-fill").style.width = state.rage + "%";
  $("rage-pct").textContent = state.rage + "%";
}

// ---------- end ----------
function endGame() {
  show("screen-end");
  $("end-score").textContent = state.score;
  const rank = clientRank(state.score);
  $("end-rank").textContent = rank.title;
  $("end-line").textContent = rank.line;
}

function clientRank(s) {
  const ranks = [
    [900, "SUBVERSION OVERLORD", "You have transcended the grind. LeetCode fears you now."],
    [650, "CERTIFIED MENACE", "The judge filed a restraining order. Framed it. Beautiful."],
    [400, "PROFESSIONAL CHEESE ARTISAN", "return true; and you never looked back."],
    [200, "FAANG REJECT (PROUD)", "Rejected with style. That's the whole win, actually."],
    [1, "STILL GRINDING", "You did some damage. The owl noticed. Keep hating."],
    [-1e9, "TRAITOR (YOU SOLVED THEM HONESTLY)", "You actually tried to solve them. In THIS economy? Shameful."],
  ];
  for (const [min, title, line] of ranks) if (s >= min) return { title, line };
  return { title: ranks[ranks.length - 1][1], line: ranks[ranks.length - 1][2] };
}

async function saveScore() {
  const name = ($("player-name").value || "anon").trim();
  try {
    const res = await api("/api/leaderboard", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, score: state.score }),
    });
    renderLeaderboard(res.entries, name, state.score);
    $("lb-modal").classList.remove("hidden");
  } catch (err) {
    alert("Even the leaderboard rejected you: " + err);
  }
}

async function openLeaderboard() {
  try {
    const res = await api("/api/leaderboard");
    renderLeaderboard(res.entries, null, null);
  } catch (_) {
    $("lb-list").innerHTML = "<li>the wall is empty. be the first to fail publicly.</li>";
  }
  $("lb-modal").classList.remove("hidden");
}

function renderLeaderboard(entries, meName, meScore) {
  const ol = $("lb-list");
  if (!entries || !entries.length) {
    ol.innerHTML = "<li>the wall is empty. be the first to fail publicly.</li>";
    return;
  }
  ol.innerHTML = "";
  entries.forEach((e, i) => {
    const li = document.createElement("li");
    if (meName !== null && e.name === meName && e.score === meScore) li.className = "me";
    li.innerHTML = `<span class="who">#${i + 1} ${escapeHtml(e.name)}<small>${escapeHtml(e.rank || "")}</small></span>`
      + `<span class="pts">${e.score}</span>`;
    ol.appendChild(li);
  });
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// ---------- wire up ----------
$("btn-start").onclick = startGame;
$("btn-again").onclick = startGame;
$("btn-next").onclick = nextRound;
$("btn-freeform").onclick = submitFreeform;
$("freeform").addEventListener("keydown", (e) => { if (e.key === "Enter") submitFreeform(); });
$("btn-save").onclick = saveScore;
$("btn-lb").onclick = openLeaderboard;
$("btn-lb-close").onclick = () => $("lb-modal").classList.add("hidden");
$("player-name").addEventListener("keydown", (e) => { if (e.key === "Enter") saveScore(); });

loadConfig();
