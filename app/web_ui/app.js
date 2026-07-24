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
  try {
    const r = await fetch("/api/login", { method: "POST", body, credentials: "include" });
    if (!r.ok) throw new Error((await r.json()).detail || "login failed");
    const data = await r.json();
    $("whoami").textContent = data.user_id;
    if (!data.hsk_level) show("onboard");
    else enterApp();
  } catch (err) {
    $("login-error").textContent = String(err.message || err);
    $("login-error").hidden = false;
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
    const stats = await (await api("/api/stats")).json();
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
function selectTab(which) {
  const coach = which === "coach";
  $("tab-coach").classList.toggle("active", coach);
  $("tab-voice").classList.toggle("active", !coach);
  $("coach-pane").hidden = !coach;
  $("voice-pane").hidden = coach;
}
$("tab-coach").addEventListener("click", () => selectTab("coach"));
$("tab-voice").addEventListener("click", () => selectTab("voice"));

// ---- shared rendering ----------------------------------------------------- //
const HANZI = /[一-鿿]/;

function addTurn(container, role, text, { withPinyin = false } = {}) {
  const turn = document.createElement("div");
  turn.className = `turn ${role}`;
  turn.innerHTML = `<div class="role">${role === "user" ? "you" : "coach"}</div><div class="body"></div>`;
  turn.querySelector(".body").textContent = text;
  if (withPinyin && HANZI.test(text)) {
    const py = document.createElement("div");
    py.className = "pinyin";
    py.textContent = "…";
    turn.appendChild(py);
    api(`/api/pinyin?text=${encodeURIComponent(text)}`)
      .then((r) => r.json()).then((d) => (py.textContent = d.pinyin))
      .catch(() => (py.textContent = ""));
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

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    chunks = [];
    mediaRecorder.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    mediaRecorder.onstop = () => { stream.getTracks().forEach((t) => t.stop()); sendTurn(); };
    mediaRecorder.start();
    $("record-btn").classList.add("recording");
    $("voice-status").textContent = "listening…";
  } catch (err) {
    $("voice-status").textContent = "mic error: " + (err.message || err);
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") mediaRecorder.stop();
  $("record-btn").classList.remove("recording");
}

async function sendTurn() {
  if (!chunks.length) { $("voice-status").textContent = "didn't catch that — try again"; return; }
  const blob = new Blob(chunks, { type: mediaRecorder.mimeType || "audio/webm" });
  const form = new FormData();
  form.append("audio", blob, "turn.webm");
  $("voice-status").textContent = "thinking…";
  try {
    const r = await api("/api/voice/turn", { method: "POST", body: form });
    const data = await r.json();
    if (!data.user_text) { $("voice-status").textContent = "didn't catch that — try again"; return; }
    addTurn($("voice-transcript"), "user", data.user_text, { withPinyin: true });
    const reply = addTurn($("voice-transcript"), "assistant", data.assistant_text, { withPinyin: true });
    markLogged(reply, data.logged);
    if (data.audio_b64) {
      $("reply-audio").src = "data:audio/mp3;base64," + data.audio_b64;
      $("reply-audio").play().catch(() => {});
    }
    $("voice-status").textContent = "your turn — hold to speak";
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
