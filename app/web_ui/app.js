"use strict";
/*
 * Unified Mandarin Coach client: login/onboarding, the text coach (/api/chat), and
 * the turn-based voice partner (/api/voice/turn — record audio, get transcripts +
 * spoken reply back). Replaces the Chainlit UI.
 */

const $ = (id) => document.getElementById(id);
const views = { login: $("login-view"), onboard: $("onboard-view"), app: $("app-view") };

function show(view) {
  Object.values(views).forEach((v) => (v.hidden = true));
  views[view].hidden = false;
}

// A stable per-browser conversation key for the text coach's LangGraph memory.
function threadId() {
  let t = localStorage.getItem("coach_thread");
  if (!t) { t = (crypto.randomUUID && crypto.randomUUID()) || String(Date.now()) + Math.random(); localStorage.setItem("coach_thread", t); }
  return t;
}

async function api(path, opts = {}) {
  const r = await fetch(path, { credentials: "include", ...opts });
  if (r.status === 401) { show("login"); throw new Error("not logged in"); }
  return r;
}

// ---- login / onboarding --------------------------------------------------- //
$("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("login-error").hidden = true;
  const body = new URLSearchParams({ username: $("username").value, password: $("password").value });
  // Time the request out so a stalled/queued connection can never leave the user
  // staring at a dead button with no feedback (see: browser keep-alive starvation).
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 15000);
  try {
    const r = await fetch("/api/login", { method: "POST", body, credentials: "include", signal: ctrl.signal });
    if (!r.ok) {
      // The body may be plain text (500/503) — read robustly so we never surface a
      // cryptic "Unexpected token …is not valid JSON" or hang the user with no message.
      let msg = `login failed (HTTP ${r.status})`;
      try { const j = await r.clone().json(); if (j && j.detail) msg = j.detail; }
      catch { const t = (await r.text().catch(() => "")).trim(); if (t) msg = t; }
      throw new Error(msg);
    }
    const data = await r.json();
    $("whoami").textContent = data.user_id;
    if (!data.hsk_level) show("onboard");
    else enterApp();
  } catch (err) {
    $("login-error").textContent = err.name === "AbortError"
      ? "Login timed out — the request never got a response. Fully close this tab (or quit Chrome) and reopen; a stale connection may be stuck."
      : String(err.message || err);
    $("login-error").hidden = false;
  } finally {
    clearTimeout(timer);
  }
});

document.querySelectorAll(".hsk-options button").forEach((b) =>
  b.addEventListener("click", async () => {
    await api("/api/profile", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ hsk_level: b.dataset.hsk }),
    });
    enterApp();
  })
);

async function enterApp() {
  show("app");
  try {
    // Plain fetch (not api()): this is a non-fatal welcome-stat lookup, so a hiccup
    // here must never trip api()'s global 401 handler and bounce us back to login.
    const r = await fetch("/api/stats", { credentials: "include" });
    if (!r.ok) return;
    const stats = await r.json();
    if (stats.total > 0) {
      const top = Object.keys(stats.by_category)[0];
      $("welcome").textContent = `Welcome back — ${stats.total} logged errors so far` + (top ? `, most common: ${top}.` : ".");
      $("welcome").hidden = false;
    }
  } catch { /* non-fatal */ }
  updateTopbar();
  restoreChatHistory();  // bring back the text-coach conversation if the server still has it
}

// Repopulate the text-coach transcript from the server's in-memory history (survives a
// reload within a server session). Best-effort and idempotent — bails if turns already exist.
async function restoreChatHistory() {
  if ($("chat").querySelector(".turn")) return;
  let data;
  try { data = await (await api(`/api/chat/history?thread_id=${encodeURIComponent(threadId())}`)).json(); }
  catch { return; }
  const msgs = (data && data.messages) || [];
  if (!msgs.length) return;
  const empty = $("chat").querySelector(".chat-empty");
  if (empty) empty.remove();
  msgs.forEach((m) => {
    if (m.role === "user") {
      addTurn($("chat"), "user", m.content);
    } else {
      const turn = addTurn($("chat"), "assistant", "");
      renderCoachBody(turn, m.content);
      addCopyButton(turn);
    }
  });
  $("chat").scrollTop = $("chat").scrollHeight;
}

// The top bar holds the welcome stat (left) and, on the Text-coach tab, the pīnyīn switch
// (right). Collapse the whole bar when neither is showing, so it never leaves an empty strip.
function updateTopbar() {
  $("topbar").hidden = $("welcome").hidden && $("coach-pinyin").hidden;
}

$("logout").addEventListener("click", async () => {
  await fetch("/api/logout", { method: "POST", credentials: "include" });
  show("login");
});

// ---- theme (light/dark) --------------------------------------------------- //
// The <head> script already applied any saved choice before paint; here we just keep
// the toggle icon in sync and let the user flip + persist it.
function effectiveTheme() {
  return document.documentElement.getAttribute("data-theme")
    || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
}
function syncThemeIcon() {
  // Show the action, not the state: a moon when we're light (click → dark), sun when dark.
  $("theme-toggle").textContent = effectiveTheme() === "dark" ? "☀️" : "🌙";
}
syncThemeIcon();
$("theme-toggle").addEventListener("click", () => {
  const next = effectiveTheme() === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
  syncThemeIcon();
});

// ---- tabs ----------------------------------------------------------------- //
const TABS = { pronounce: "pronounce-pane", coach: "coach-pane", voice: "voice-pane", progress: "progress-pane" };
function selectTab(which) {
  for (const [name, pane] of Object.entries(TABS)) {
    $(`tab-${name}`).classList.toggle("active", name === which);
    $(pane).hidden = name !== which;
  }
  $("coach-pinyin").hidden = which !== "coach";  // the pīnyīn switch belongs to the text coach
  updateTopbar();
  // Focus the pane's primary input so the learner can type immediately (voice has no field).
  const focusTarget = which === "coach" ? "chat-input" : which === "pronounce" ? "pron-input" : null;
  if (focusTarget) $(focusTarget).focus();
  if (which === "progress") loadProgress();  // refresh each time it's opened
}

// ---- progress (errors dashboard) ------------------------------------------ //
// Fetch the corpus stats + recent errors and render a category breakdown (with trend)
// plus a recent-corrections list. Rebuilt each time the tab opens so it stays current.
async function loadProgress() {
  const body = $("progress-body");
  body.textContent = "Loading…";
  let stats, errs;
  try {
    stats = await (await api("/api/stats")).json();
    errs = await (await api("/api/errors?limit=25")).json();
  } catch { body.textContent = "Couldn't load your progress — try again."; return; }
  body.textContent = "";

  if (!stats || !stats.total) {
    const p = document.createElement("p");
    p.className = "progress-empty muted";
    p.textContent = "No logged errors yet. Chat with the coach or practise pronunciation, "
      + "and the recurring mistakes we catch will collect here.";
    body.appendChild(p);
    return;
  }

  const total = document.createElement("div");
  total.className = "stat-total";
  total.textContent = `${stats.total} logged ${stats.total === 1 ? "error" : "errors"}`;
  body.appendChild(total);

  // Category breakdown: a bar per category, with a trend arrow (up = getting worse).
  const cats = Object.entries(stats.by_category);
  const max = Math.max(...cats.map(([, c]) => c), 1);
  const list = document.createElement("div");
  list.className = "cat-list";
  cats.forEach(([cat, count]) => {
    const row = document.createElement("div"); row.className = "cat-row";
    const name = document.createElement("div"); name.className = "cat-name"; name.textContent = cat.replace(/_/g, " ");
    const bar = document.createElement("div"); bar.className = "cat-bar";
    const fill = document.createElement("span"); fill.style.width = `${(count / max) * 100}%`; bar.appendChild(fill);
    const meta = document.createElement("div"); meta.className = "cat-meta";
    meta.appendChild(document.createTextNode(`${count} `));
    const trend = (stats.trend || {})[cat];
    const t = document.createElement("span");
    t.className = trend === "increasing" ? "trend-up" : trend === "decreasing" ? "trend-down" : "";
    t.textContent = trend === "increasing" ? "↑" : trend === "decreasing" ? "↓" : "→";
    t.title = trend === "increasing" ? "happening more lately" : trend === "decreasing" ? "improving" : "steady";
    meta.appendChild(t);
    row.append(name, bar, meta);
    list.appendChild(row);
  });
  body.appendChild(list);

  // Recent corrections.
  const h = document.createElement("h2"); h.textContent = "Recent corrections"; body.appendChild(h);
  const errList = document.createElement("div"); errList.className = "err-list";
  (errs.errors || []).forEach((e) => {
    const card = document.createElement("div"); card.className = "err-card";
    const head = document.createElement("div"); head.className = "err-head";
    const cat = document.createElement("span"); cat.className = "err-cat"; cat.textContent = (e.category || "").replace(/_/g, " ");
    head.appendChild(cat);
    if (e.source === "voice") { const b = document.createElement("span"); b.className = "badge-voice"; b.textContent = "voice"; head.appendChild(b); }
    card.appendChild(head);
    const fix = document.createElement("p"); fix.className = "err-fix";
    const wrong = document.createElement("span"); wrong.className = "wrong"; wrong.textContent = e.original || "—";
    const right = document.createElement("span"); right.className = "right"; right.textContent = e.correction || "—";
    fix.append(wrong, document.createTextNode("  →  "), right);
    card.appendChild(fix);
    if (e.explanation) { const ex = document.createElement("p"); ex.className = "err-note"; ex.textContent = e.explanation; card.appendChild(ex); }
    errList.appendChild(card);
  });
  body.appendChild(errList);
}
Object.keys(TABS).forEach((name) => $(`tab-${name}`).addEventListener("click", () => selectTab(name)));

// ---- shared rendering ----------------------------------------------------- //
const HANZI = /[一-鿿]/;

// Render 汉字 with pīnyīn underneath each character, inline, via <ruby>. Built with the
// DOM (not innerHTML) so model/transcript text can never inject markup. Non-Han runs
// (punctuation, latin) pass through as plain text so the sentence still reads naturally.
// Turn aligned pīnyīn segments into DOM nodes: one <ruby>汉字<rt>pīn</rt></ruby> per Han
// char, plain text for the non-Han runs. Built with the DOM so text can't inject markup.
function segmentsToNodes(segments) {
  return segments.map((s) => {
    if (s.hanzi) {
      const ruby = document.createElement("ruby");
      ruby.appendChild(document.createTextNode(s.hanzi));
      const rt = document.createElement("rt");
      rt.textContent = s.pinyin || "";
      ruby.appendChild(rt);
      return ruby;
    }
    return document.createTextNode(s.text || "");
  });
}

function renderRuby(bodyEl, segments) {
  bodyEl.textContent = "";
  bodyEl.classList.add("ruby");
  segmentsToNodes(segments).forEach((n) => bodyEl.appendChild(n));
}

// Look up aligned pīnyīn for a string, cached (the same example sentence recurs, and the
// toggle re-renders existing turns — no point re-fetching). Resolves to segments or null.
const _pinyinCache = new Map();
function fetchSegments(text) {
  if (_pinyinCache.has(text)) return Promise.resolve(_pinyinCache.get(text));
  return api(`/api/pinyin?text=${encodeURIComponent(text)}`)
    .then((r) => r.json())
    .then((d) => { const segs = d.segments || null; if (segs) _pinyinCache.set(text, segs); return segs; })
    .catch(() => null);
}

// Walk a rendered subtree and replace every Han-bearing text node with ruby (汉字 over
// pīnyīn). Skips code/pre (verbatim) and anything already rubied. Fetches are async and
// best-effort — a failure leaves the plain hanzi in place.
const _RUBY_SKIP = new Set(["CODE", "PRE", "RUBY", "RT"]);
function rubifyHanzi(root) {
  const targets = [];
  (function walk(node) {
    Array.from(node.childNodes).forEach((child) => {
      if (child.nodeType === 3) { if (HANZI.test(child.nodeValue)) targets.push(child); }
      else if (child.nodeType === 1 && !_RUBY_SKIP.has(child.tagName)) walk(child);
    });
  })(root);
  targets.forEach((node) => {
    fetchSegments(node.nodeValue).then((segs) => {
      if (!segs || !node.parentNode) return;
      const frag = document.createDocumentFragment();
      segmentsToNodes(segs).forEach((n) => frag.appendChild(n));
      node.parentNode.replaceChild(frag, node);
    });
  });
}

function addTurn(container, role, text, { withPinyin = false, segments = null, coach = false } = {}) {
  const turn = document.createElement("div");
  turn.className = `turn ${role}${coach ? " coach" : ""}`;
  const label = coach ? "coach · explanation" : role === "user" ? "you" : "coach";
  turn.innerHTML = `<div class="role">${label}</div><div class="body"></div>`;
  const body = turn.querySelector(".body");
  body.textContent = text;
  if (withPinyin && HANZI.test(text)) {
    if (segments) {
      renderRuby(body, segments);  // already have alignment (voice turn) — no flicker/fetch
    } else {
      // Fallback: fetch the aligned segments, then swap plain text -> ruby.
      api(`/api/pinyin?text=${encodeURIComponent(text)}`)
        .then((r) => r.json()).then((d) => d.segments && renderRuby(body, d.segments))
        .catch(() => {});
    }
  }
  container.appendChild(turn);
  container.scrollTop = container.scrollHeight;
  return turn;
}

// Render a small, safe Markdown subset (the coach replies in Markdown: **bold** for
// corrections, bullet/numbered lists for drills, `code`, headings, example sentences).
// Built with the DOM — model text only ever becomes textContent, so nothing it emits can
// inject markup (same discipline as renderRuby). Deliberately does NOT treat `_` as
// emphasis: the coach names tools like error_pattern_analyser and snake_case must survive.
function appendInline(parent, text) {
  const re = /`([^`]+)`|\*\*([^*]+)\*\*|\*([^*]+)\*|\[([^\]]+)\]\(([^)\s]+)\)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) parent.appendChild(document.createTextNode(text.slice(last, m.index)));
    let el;
    if (m[1] != null) { el = document.createElement("code"); el.textContent = m[1]; }
    else if (m[2] != null) { el = document.createElement("strong"); el.textContent = m[2]; }
    else if (m[3] != null) { el = document.createElement("em"); el.textContent = m[3]; }
    else { // link — only http(s) or root-relative hrefs; anything else stays plain text
      el = document.createElement("a"); el.textContent = m[4];
      if (/^(https?:\/\/|\/)/i.test(m[5])) { el.href = m[5]; el.target = "_blank"; el.rel = "noopener noreferrer"; }
    }
    parent.appendChild(el);
    last = re.lastIndex;
  }
  if (last < text.length) parent.appendChild(document.createTextNode(text.slice(last)));
}

function renderMarkdown(bodyEl, src) {
  bodyEl.textContent = "";
  bodyEl.classList.add("md");
  const lines = String(src || "").replace(/\r\n?/g, "\n").split("\n");
  const isBlank = (l) => /^\s*$/.test(l);
  const isFence = (l) => /^\s*```/.test(l);
  const isHeading = (l) => /^#{1,6}\s+/.test(l);
  const isUl = (l) => /^\s*[-*+]\s+/.test(l);
  const isOl = (l) => /^\s*\d+\.\s+/.test(l);
  const isHr = (l) => /^\s*([-*_])(\s*\1){2,}\s*$/.test(l);           // ---  ***  ___
  const isQuote = (l) => /^\s*>\s?/.test(l);                          // > blockquote
  const isTableSep = (l) => /^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)+\|?\s*$/.test(l);
  const cells = (l) => l.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (isBlank(line)) { i++; continue; }
    if (isFence(line)) {                                   // ``` fenced code block
      i++;
      const buf = [];
      while (i < lines.length && !isFence(lines[i])) { buf.push(lines[i]); i++; }
      i++;  // consume the closing fence
      const pre = document.createElement("pre");
      const code = document.createElement("code");
      code.textContent = buf.join("\n");
      pre.appendChild(code); bodyEl.appendChild(pre);
      continue;
    }
    if (isHr(line)) { bodyEl.appendChild(document.createElement("hr")); i++; continue; }
    if (isQuote(line)) {                                   // > blockquote (one <p> per line)
      const bq = document.createElement("blockquote");
      while (i < lines.length && isQuote(lines[i])) {
        const p = document.createElement("p");
        appendInline(p, lines[i].replace(/^\s*>\s?/, ""));
        bq.appendChild(p); i++;
      }
      bodyEl.appendChild(bq); continue;
    }
    // GFM table: a `| … |` header row immediately followed by a `|---|---|` separator.
    if (line.includes("|") && i + 1 < lines.length && isTableSep(lines[i + 1])) {
      const table = document.createElement("table");
      const thead = document.createElement("thead");
      const htr = document.createElement("tr");
      cells(line).forEach((c) => { const th = document.createElement("th"); appendInline(th, c); htr.appendChild(th); });
      thead.appendChild(htr); table.appendChild(thead);
      i += 2;  // consume header + separator
      const tbody = document.createElement("tbody");
      while (i < lines.length && !isBlank(lines[i]) && lines[i].includes("|")) {
        const tr = document.createElement("tr");
        cells(lines[i]).forEach((c) => { const td = document.createElement("td"); appendInline(td, c); tr.appendChild(td); });
        tbody.appendChild(tr); i++;
      }
      table.appendChild(tbody); bodyEl.appendChild(table);
      continue;
    }
    const h = line.match(/^(#{1,6})\s+(.*)$/);             // # heading (capped to h3/h4)
    if (h) {
      const el = document.createElement(h[1].length <= 1 ? "h3" : "h4");
      appendInline(el, h[2].trim());
      bodyEl.appendChild(el); i++; continue;
    }
    if (isUl(line) || isOl(line)) {                        // - / 1. lists
      const ordered = isOl(line);
      const list = document.createElement(ordered ? "ol" : "ul");
      const match = ordered ? isOl : isUl;
      const strip = ordered ? /^\s*\d+\.\s+/ : /^\s*[-*+]\s+/;
      while (i < lines.length && match(lines[i])) {
        const li = document.createElement("li");
        appendInline(li, lines[i].replace(strip, ""));
        list.appendChild(li); i++;
      }
      bodyEl.appendChild(list); continue;
    }
    const para = [];                                       // paragraph (soft breaks -> <br>)
    const startsTable = (n) => lines[n].includes("|") && n + 1 < lines.length && isTableSep(lines[n + 1]);
    while (i < lines.length && !isBlank(lines[i]) && !isFence(lines[i]) && !isHr(lines[i])
           && !isQuote(lines[i]) && !isHeading(lines[i]) && !isUl(lines[i]) && !isOl(lines[i]) && !startsTable(i)) {
      para.push(lines[i]); i++;
    }
    const p = document.createElement("p");
    para.forEach((ln, idx) => { if (idx) p.appendChild(document.createElement("br")); appendInline(p, ln); });
    bodyEl.appendChild(p);
  }
}

// One shared "logged to your error corpus" chip, used by the chat, pronounce and voice
// panes so the same event looks the same everywhere. The 📝 comes from CSS (::before).
function loggedChip(text) {
  const el = document.createElement("div");
  el.className = "logged";
  el.textContent = text;
  return el;
}

function markLogged(turn, logged) {
  if (!logged) return;
  turn.appendChild(loggedChip(`logged (${logged.category}): ${logged.original} → ${logged.correction}`));
}

// ---- text coach ----------------------------------------------------------- //
// A live "…" typing indicator (animated dots) for the pending reply. Built with the DOM
// so it swaps cleanly for the real answer once renderMarkdown clears the body.
function showThinking(bodyEl) {
  bodyEl.textContent = "";
  const dots = document.createElement("span");
  dots.className = "typing";
  for (let i = 0; i < 3; i++) dots.appendChild(document.createElement("span"));
  bodyEl.appendChild(dots);
}

// Render a coach reply's Markdown, then (when the pīnyīn toggle is on) rubify its Chinese.
// The raw Markdown is stashed on the turn so the toggle can re-render in place, and the
// toggle re-runs this over every existing coach turn — hence the pinyin fetch cache above.
let showPinyin = localStorage.getItem("coach_pinyin") !== "off";  // default on (learner-first)
function renderCoachBody(turn, md) {
  if (md != null) turn._md = md;
  const body = turn.querySelector(".body");
  renderMarkdown(body, turn._md);
  body.classList.toggle("pinyin", showPinyin);
  if (showPinyin) rubifyHanzi(body);
}

// A hover "copy" affordance on a coach reply. Copies the raw Markdown (clean hanzi + text,
// no ruby interleaving) — what a learner wants when grabbing a corrected sentence or drill.
// Appended to the turn (not the body), so it survives a pīnyīn re-render of the body.
function addCopyButton(turn) {
  const btn = document.createElement("button");
  btn.className = "copy-btn";
  btn.type = "button";
  btn.textContent = "copy";
  btn.addEventListener("click", () => {
    const text = turn._md || turn.querySelector(".body").innerText || "";
    navigator.clipboard.writeText(text).then(() => {
      btn.textContent = "copied ✓";
      setTimeout(() => { btn.textContent = "copy"; }, 1200);
    }).catch(() => { btn.textContent = "copy failed"; });
  });
  turn.appendChild(btn);
}

// Grow a textarea to fit its content (capped by the CSS max-height, which then scrolls),
// so a multi-line message isn't trapped in a one-row slot.
function autoGrow(el) {
  el.style.height = "auto";
  el.style.height = el.scrollHeight + "px";
}

const chatForm = $("chat-form");
const chatSend = chatForm.querySelector("button[type=submit]");
let chatBusy = false;  // guards against a double-submit (Enter + click, or a fast second Enter)

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (chatBusy) return;
  const input = $("chat-input");
  const msg = input.value.trim();
  if (!msg) return;
  input.value = "";
  autoGrow(input);  // collapse the box back to one row after clearing it
  const emptyHint = $("chat").querySelector(".chat-empty");
  if (emptyHint) emptyHint.remove();
  addTurn($("chat"), "user", msg);
  const pending = addTurn($("chat"), "assistant", "");
  showThinking(pending.querySelector(".body"));
  chatBusy = true;
  chatSend.disabled = true;
  try {
    const r = await api("/api/chat", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, thread_id: threadId() }),
    });
    const data = await r.json();
    renderCoachBody(pending, data.answer);
    markLogged(pending, data.logged);
    addCopyButton(pending);
  } catch (err) {
    pending.querySelector(".body").textContent = "Error: " + (err.message || err);
  } finally {
    chatBusy = false;
    chatSend.disabled = false;
  }
  $("chat").scrollTop = $("chat").scrollHeight;
  input.focus();  // keep the learner typing — don't leave focus on the Send button
});

$("chat-input").addEventListener("input", (e) => autoGrow(e.target));
$("pron-input").addEventListener("input", (e) => autoGrow(e.target));  // same behaviour on the pronounce composer

// Enter sends; Shift+Enter inserts a newline (standard chat UX). The box is a <textarea>,
// so without this Enter would just add a line and the user has to reach for the Send button.
$("chat-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.requestSubmit();
  }
});

// 拼音 toggle: show/hide pīnyīn under the coach's Chinese. Re-renders every existing coach
// turn in place (cheap — Markdown is re-parsed from the stashed source, pinyin is cached).
const pinyinToggle = $("coach-pinyin");
function reflectPinyinToggle() {
  pinyinToggle.classList.toggle("on", showPinyin);
  pinyinToggle.setAttribute("aria-checked", showPinyin ? "true" : "false");
}
reflectPinyinToggle();
pinyinToggle.addEventListener("click", () => {
  showPinyin = !showPinyin;
  localStorage.setItem("coach_pinyin", showPinyin ? "on" : "off");
  reflectPinyinToggle();
  $("chat").querySelectorAll(".turn.assistant").forEach((turn) => {
    if (turn._md != null) renderCoachBody(turn);
  });
});

// ---- voice partner (hold to speak) ---------------------------------------- //
let mediaRecorder = null;
let chunks = [];
let voiceMode = "auto";  // auto | converse | coach — the response-mode toggle

// `capturing` guards against a double-start (e.g. mousedown AND spacebar) — it flips
// synchronously, before the async getUserMedia, so a second trigger is a no-op.
let capturing = false;

async function startRecording() {
  if (capturing) return;
  capturing = true;
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    chunks = [];
    mediaRecorder.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    mediaRecorder.onstop = () => { stream.getTracks().forEach((t) => t.stop()); sendTurn(); };
    mediaRecorder.start();
    $("record-btn").classList.add("recording");
    $("voice-status").textContent = "listening… release to send";
  } catch (err) {
    capturing = false;
    $("voice-status").textContent = "mic error: " + (err.message || err);
  }
}

function stopRecording() {
  if (!capturing) return;
  capturing = false;
  if (mediaRecorder && mediaRecorder.state !== "inactive") mediaRecorder.stop();
  $("record-btn").classList.remove("recording");
}

// Fetch the reply audio from /api/voice/speak and play it. This is split out of the turn so the
// transcript + reply text render the MOMENT the brain is done (~2s sooner than the old path,
// which waited on TTS before showing anything). Audio is best-effort — any failure is silent and
// the text stands. (We deliberately don't do MediaSource chunk-streaming: gpt-4o-mini-tts's
// latency is front-loaded — first byte lands ~2s in even when streaming — so incremental playback
// buys ~0.4s while adding real browser-quirk risk. The text-early decouple is the actual win.)
async function speakReply(text) {
  if (!text) return;
  try {
    const resp = await fetch("/api/voice/speak", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!resp.ok) return;
    const audio = $("reply-audio");
    audio.src = URL.createObjectURL(await resp.blob());
    audio.play().catch(() => {});
  } catch (_e) {
    /* audio is best-effort; the reply text is already on screen */
  }
}

async function sendTurn() {
  if (!chunks.length) { $("voice-status").textContent = "didn't catch that — try again"; return; }
  const blob = new Blob(chunks, { type: mediaRecorder.mimeType || "audio/webm" });
  const form = new FormData();
  form.append("audio", blob, "turn.webm");
  form.append("mode", voiceMode);
  $("voice-status").textContent = "thinking…";
  try {
    const r = await api("/api/voice/turn", { method: "POST", body: form });
    const data = await r.json();
    if (!data.user_text) { $("voice-status").textContent = "didn't catch that — try again"; return; }
    const isCoach = data.intent === "coach";
    addTurn($("voice-transcript"), "user", data.user_text, { withPinyin: true, segments: data.user_segments });
    const reply = addTurn($("voice-transcript"), "assistant", data.assistant_text,
      { withPinyin: true, segments: data.assistant_segments, coach: isCoach });
    markLogged(reply, data.logged);
    // Text is on screen now; the audio streams in behind it (best-effort — never block the turn).
    $("voice-status").textContent = "your turn — hold to speak";
    speakReply(data.spoken_text);
  } catch (err) {
    $("voice-status").textContent = "error: " + (err.message || err);
  }
}

const rec = $("record-btn");
rec.addEventListener("mousedown", startRecording);
rec.addEventListener("mouseup", stopRecording);
rec.addEventListener("mouseleave", stopRecording);
rec.addEventListener("touchstart", (e) => { e.preventDefault(); startRecording(); });
rec.addEventListener("touchend", (e) => { e.preventDefault(); stopRecording(); });

// Hold Space to talk — but only on the Voice tab and never while typing, so the
// pronounce/coach text fields keep their normal spacebar. preventDefault stays inside
// the passing branch so it can't swallow spaces anywhere else.
function typingInField(el) {
  if (!el) return false;
  const tag = el.tagName;
  return tag === "TEXTAREA" || tag === "INPUT" || el.isContentEditable;
}
function voiceActive() {
  return views.app && !views.app.hidden && !$("voice-pane").hidden;
}
document.addEventListener("keydown", (e) => {
  if (e.code !== "Space" || e.repeat) return;
  if (!voiceActive() || typingInField(e.target)) return;
  e.preventDefault();
  startRecording();
});
document.addEventListener("keyup", (e) => {
  if (e.code !== "Space") return;
  if (!voiceActive()) return;
  e.preventDefault();
  stopRecording();
});
// If focus leaves the window mid-hold, keyup may never arrive — stop so the mic
// doesn't stick on. capturing-guarded, so it's a no-op when not recording.
window.addEventListener("blur", stopRecording);

// Response-mode toggle: Auto (route by intent) / Chat (always converse) / Coach (always explain).
const modeGroup = $("voice-mode");
modeGroup.querySelectorAll("button").forEach((b) => {
  b.addEventListener("click", () => {
    voiceMode = b.dataset.mode;
    modeGroup.querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
    $("voice-status").textContent =
      voiceMode === "coach" ? "coach mode — every turn is explained"
      : voiceMode === "converse" ? "chat mode — always conversation"
      : "auto — English questions go to the coach";
  });
});

$("voice-reset").addEventListener("click", async () => {
  await api("/api/voice/reset", { method: "POST" });
  $("voice-transcript").innerHTML = "";
  $("voice-status").textContent = "conversation reset — hold to speak";
});

// ---- boot: resume an existing session if the cookie is still valid --------- //
(async () => {
  try {
    const r = await fetch("/api/profile", { credentials: "include" });
    if (r.ok) {
      const data = await r.json();
      $("whoami").textContent = data.user_id;
      if (!data.hsk_level) show("onboard"); else enterApp();
    } else { show("login"); }
  } catch { show("login"); }
})();
