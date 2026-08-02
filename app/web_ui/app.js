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
}

$("logout").addEventListener("click", async () => {
  await fetch("/api/logout", { method: "POST", credentials: "include" });
  show("login");
});

// ---- tabs ----------------------------------------------------------------- //
const TABS = { pronounce: "pronounce-pane", coach: "coach-pane", voice: "voice-pane" };
function selectTab(which) {
  for (const [name, pane] of Object.entries(TABS)) {
    $(`tab-${name}`).classList.toggle("active", name === which);
    $(pane).hidden = name !== which;
  }
}
Object.keys(TABS).forEach((name) => $(`tab-${name}`).addEventListener("click", () => selectTab(name)));

// ---- shared rendering ----------------------------------------------------- //
const HANZI = /[一-鿿]/;

// Render 汉字 with pīnyīn underneath each character, inline, via <ruby>. Built with the
// DOM (not innerHTML) so model/transcript text can never inject markup. Non-Han runs
// (punctuation, latin) pass through as plain text so the sentence still reads naturally.
function renderRuby(bodyEl, segments) {
  bodyEl.textContent = "";
  bodyEl.classList.add("ruby");
  segments.forEach((s) => {
    if (s.hanzi) {
      const ruby = document.createElement("ruby");
      ruby.appendChild(document.createTextNode(s.hanzi));
      const rt = document.createElement("rt");
      rt.textContent = s.pinyin || "";
      ruby.appendChild(rt);
      bodyEl.appendChild(ruby);
    } else {
      bodyEl.appendChild(document.createTextNode(s.text || ""));
    }
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

function markLogged(turn, logged) {
  if (!logged) return;
  const el = document.createElement("div");
  el.className = "logged";
  el.textContent = `📝 logged (${logged.category}): ${logged.original} → ${logged.correction}`;
  turn.appendChild(el);
}

// ---- text coach ----------------------------------------------------------- //
$("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = $("chat-input");
  const msg = input.value.trim();
  if (!msg) return;
  input.value = "";
  addTurn($("chat"), "user", msg);
  const pending = addTurn($("chat"), "assistant", "…");
  try {
    const r = await api("/api/chat", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, thread_id: threadId() }),
    });
    const data = await r.json();
    pending.querySelector(".body").textContent = data.answer;
    markLogged(pending, data.logged);
  } catch (err) {
    pending.querySelector(".body").textContent = "Error: " + (err.message || err);
  }
  $("chat").scrollTop = $("chat").scrollHeight;
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
