"use strict";
/*
 * Voice Conversation Partner — browser client.
 *
 * Flow: log in (cookie) -> GET /realtime/session for a short-lived OpenAI ephemeral
 * token -> open a WebRTC PeerConnection straight to OpenAI (audio never touches our
 * server) -> render transcript events (汉字 + pīnyīn) -> POST /voice/log-turn per
 * completed exchange so the error corpus grows from spoken use.
 */

const els = {
  login: document.getElementById("login"),
  loginForm: document.getElementById("login-form"),
  loginError: document.getElementById("login-error"),
  conversation: document.getElementById("conversation"),
  startBtn: document.getElementById("start-btn"),
  stopBtn: document.getElementById("stop-btn"),
  status: document.getElementById("status"),
  transcript: document.getElementById("transcript"),
  remoteAudio: document.getElementById("remote-audio"),
};

let pc = null;
let micStream = null;
// The learner's most recent completed transcript, held until the assistant replies
// so the pair can be logged together.
let pendingUser = null; // { text, confidence }

function setStatus(s) {
  els.status.textContent = s;
  console.log("[voice] status:", s);
}

// ---- auth ----------------------------------------------------------------- //
els.loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  els.loginError.hidden = true;
  const body = new URLSearchParams({
    username: document.getElementById("username").value,
    password: document.getElementById("password").value,
  });
  try {
    const r = await fetch("/voice/login", { method: "POST", body, credentials: "include" });
    if (!r.ok) throw new Error((await r.json()).detail || "login failed");
    els.login.hidden = true;
    els.conversation.hidden = false;
    setStatus("logged in — ready");
  } catch (err) {
    els.loginError.textContent = String(err.message || err);
    els.loginError.hidden = false;
  }
});

// ---- confidence from transcription logprobs ------------------------------- //
function confidenceFromLogprobs(logprobs) {
  if (!Array.isArray(logprobs) || logprobs.length === 0) return null;
  // Mean per-token probability (exp of logprob) as a rough 0–1 STT confidence.
  const probs = logprobs
    .map((lp) => (typeof lp.logprob === "number" ? Math.exp(lp.logprob) : null))
    .filter((p) => p !== null);
  if (probs.length === 0) return null;
  return probs.reduce((a, b) => a + b, 0) / probs.length;
}

// ---- transcript rendering ------------------------------------------------- //
async function renderTurn(role, hanzi) {
  const turn = document.createElement("div");
  turn.className = `turn ${role}`;
  turn.innerHTML = `<div class="role">${role}</div><div class="hanzi"></div><div class="pinyin">…</div>`;
  turn.querySelector(".hanzi").textContent = hanzi;
  els.transcript.appendChild(turn);
  els.transcript.scrollTop = els.transcript.scrollHeight;
  try {
    const r = await fetch(`/voice/pinyin?text=${encodeURIComponent(hanzi)}`, { credentials: "include" });
    if (r.ok) turn.querySelector(".pinyin").textContent = (await r.json()).pinyin;
    else turn.querySelector(".pinyin").textContent = "";
  } catch {
    turn.querySelector(".pinyin").textContent = "";
  }
}

async function logTurn(userText, assistantText, confidence) {
  try {
    const r = await fetch("/voice/log-turn", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ user_text: userText, assistant_text: assistantText, confidence }),
    });
    console.log("[voice] log-turn:", await r.json());
  } catch (err) {
    console.warn("[voice] log-turn failed:", err); // best-effort, never blocks conversation
  }
}

// ---- data channel events -------------------------------------------------- //
function handleEvent(evt) {
  // Learner's speech, transcribed by the Realtime API.
  if (evt.type === "conversation.item.input_audio_transcription.completed") {
    const text = evt.transcript || "";
    const confidence = confidenceFromLogprobs(evt.logprobs);
    pendingUser = { text, confidence };
    renderTurn("user", text);
    return;
  }
  // Assistant's spoken reply, as text. Slug has varied across API versions; match either.
  if (evt.type === "response.output_audio_transcript.done" || evt.type === "response.audio_transcript.done") {
    const assistantText = evt.transcript || "";
    renderTurn("assistant", assistantText);
    if (pendingUser) {
      logTurn(pendingUser.text, assistantText, pendingUser.confidence);
      pendingUser = null;
    }
    return;
  }
  if (evt.type === "error") console.error("[voice] realtime error:", evt);
}

// ---- start / stop --------------------------------------------------------- //
async function start() {
  els.startBtn.disabled = true;
  try {
    setStatus("requesting microphone…");
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true });

    setStatus("minting session token…");
    const sr = await fetch("/realtime/session", { credentials: "include" });
    if (!sr.ok) throw new Error((await sr.json()).detail || "session mint failed");
    const session = await sr.json();
    const secret = session.client_secret || {};
    const ephemeral = secret.value || (secret.client_secret && secret.client_secret.value);
    if (!ephemeral) throw new Error("no ephemeral token in session response");
    const model = session.model;

    setStatus("connecting…");
    pc = new RTCPeerConnection();
    pc.ontrack = (e) => { els.remoteAudio.srcObject = e.streams[0]; };
    micStream.getTracks().forEach((t) => pc.addTrack(t, micStream));

    const dc = pc.createDataChannel("oai-events");
    dc.onmessage = (e) => {
      try { handleEvent(JSON.parse(e.data)); } catch (err) { console.warn("[voice] bad event", err); }
    };
    dc.onopen = () => setStatus("connected — start speaking Mandarin");

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    const resp = await fetch(`https://api.openai.com/v1/realtime/calls?model=${encodeURIComponent(model)}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${ephemeral}`, "Content-Type": "application/sdp" },
      body: offer.sdp,
    });
    if (!resp.ok) throw new Error(`SDP exchange failed: ${resp.status} ${await resp.text()}`);
    await pc.setRemoteDescription({ type: "answer", sdp: await resp.text() });

    els.stopBtn.hidden = false;
  } catch (err) {
    console.error("[voice] start failed:", err);
    setStatus("error: " + (err.message || err));
    stop();
    els.startBtn.disabled = false;
  }
}

function stop() {
  if (pc) { pc.close(); pc = null; }
  if (micStream) { micStream.getTracks().forEach((t) => t.stop()); micStream = null; }
  els.stopBtn.hidden = true;
  els.startBtn.disabled = false;
  setStatus("ended");
}

els.startBtn.addEventListener("click", start);
els.stopBtn.addEventListener("click", stop);
