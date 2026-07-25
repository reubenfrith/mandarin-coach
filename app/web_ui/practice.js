"use strict";
/*
 * Pronunciation coach UI (the "Pronounce" tab). Two passes:
 *   1. compose your OWN sentence -> /api/pronounce/correct -> corrected target (+ hear it)
 *   2. record yourself saying it -> /api/pronounce/assess -> tone score + pitch overlay
 *
 * Audio is encoded to WAV in the browser (decode the MediaRecorder blob, re-encode PCM)
 * so the server never has to decode webm/opus. Reuses `$` and `api` from app.js.
 */

const P = { corrected: "", recording: false, mr: null, chunks: [], stream: null, takeUrl: null };

// ---- WAV encoding (so the server gets clean PCM, per plan decision 1) ------ //
function floatToWav(samples, sampleRate) {
  const n = samples.length;
  const dv = new DataView(new ArrayBuffer(44 + n * 2));
  const str = (o, s) => { for (let i = 0; i < s.length; i++) dv.setUint8(o + i, s.charCodeAt(i)); };
  str(0, "RIFF"); dv.setUint32(4, 36 + n * 2, true); str(8, "WAVE");
  str(12, "fmt "); dv.setUint32(16, 16, true); dv.setUint16(20, 1, true); dv.setUint16(22, 1, true);
  dv.setUint32(24, sampleRate, true); dv.setUint32(28, sampleRate * 2, true);
  dv.setUint16(32, 2, true); dv.setUint16(34, 16, true);
  str(36, "data"); dv.setUint32(40, n * 2, true);
  let o = 44;
  for (let i = 0; i < n; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    dv.setInt16(o, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    o += 2;
  }
  return new Blob([dv], { type: "audio/wav" });
}

async function blobToWav(blob) {
  const AC = window.AudioContext || window.webkitAudioContext;
  const ctx = new AC();
  const buf = await ctx.decodeAudioData(await blob.arrayBuffer());
  const len = buf.length, ch = buf.numberOfChannels;
  const mono = new Float32Array(len);
  for (let c = 0; c < ch; c++) {
    const d = buf.getChannelData(c);
    for (let i = 0; i < len; i++) mono[i] += d[i] / ch;  // downmix
  }
  const wav = floatToWav(mono, buf.sampleRate);
  ctx.close();
  return wav;
}

// ---- rendering ------------------------------------------------------------ //
function renderSyllables(container, syllables) {
  container.innerHTML = "";
  syllables.forEach((s) => {
    let cls = "neutral";
    if (s.ok === true) cls = s.weak ? "weak" : "good";
    else if (s.ok === false) cls = "bad";
    const chip = document.createElement("div");
    chip.className = "syl " + cls;
    let sub = `${s.pinyin} · T${s.tone}`;
    if (s.ok === false && s.predicted_tone) sub += ` → T${s.predicted_tone}`;
    chip.innerHTML = `<div class="h"></div><div class="p"></div>`;
    chip.querySelector(".h").textContent = s.hanzi;
    chip.querySelector(".p").textContent = sub;
    container.appendChild(chip);
  });
}

function drawCurves(canvas, learner, target) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height, pad = 12;
  ctx.clearRect(0, 0, W, H);
  const all = [...(learner || []), ...(target || [])].filter(Number.isFinite);
  if (!all.length) return;
  let lo = Math.min(...all), hi = Math.max(...all);
  if (hi - lo < 0.2) { lo -= 0.5; hi += 0.5; }
  const x = (i, n) => pad + (i / (n - 1)) * (W - 2 * pad);
  const y = (v) => H - pad - ((v - lo) / (hi - lo)) * (H - 2 * pad);
  const line = (arr, color, w) => {
    if (!arr || arr.length < 2) return;
    ctx.strokeStyle = color; ctx.lineWidth = w; ctx.lineJoin = "round"; ctx.beginPath();
    arr.forEach((v, i) => { const px = x(i, arr.length), py = y(v); i ? ctx.lineTo(px, py) : ctx.moveTo(px, py); });
    ctx.stroke();
  };
  line(target, "#9aa1a8", 3);
  line(learner, "#b3282d", 3);
}

function renderLogged(container, logged) {
  container.innerHTML = "";
  (logged || []).forEach((l) => {
    const el = document.createElement("div");
    el.className = "logged";
    el.textContent = `📝 logged: ${l.hanzi} — ${l.explanation}`;
    container.appendChild(el);
  });
}

// ---- Pass 1: compose & correct -------------------------------------------- //
$("pron-check").addEventListener("click", async () => {
  const text = $("pron-input").value.trim();
  if (!text) return;
  $("pron-check").disabled = true;
  $("pron-status").textContent = "";
  try {
    const fd = new FormData(); fd.append("text", text);
    const data = await (await api("/api/pronounce/correct", { method: "POST", body: fd })).json();
    P.corrected = data.corrected;
    $("pron-correction").textContent = data.had_error
      ? `✏️ ${data.original}  →  ${data.corrected}` + (data.note ? `  (${data.note})` : "")
      : `✓ ${data.corrected}`;
    renderSyllables($("pron-syllables"), data.syllables);
    $("pron-target-box").hidden = false;
    $("pron-results").hidden = true;
    // New sentence — drop the previous take so playback can't replay a stale one.
    if (P.takeUrl) { URL.revokeObjectURL(P.takeUrl); P.takeUrl = null; $("pron-take-audio").removeAttribute("src"); }
    $("pron-playback").hidden = true;
    $("pron-status").textContent = "Hear it, then record yourself saying it.";
  } catch (e) {
    $("pron-status").textContent = "Error: " + (e.message || e);
  }
  $("pron-check").disabled = false;
});

$("pron-hear").addEventListener("click", async () => {
  if (!P.corrected) return;
  $("pron-status").textContent = "loading audio…";
  try {
    const fd = new FormData(); fd.append("text", P.corrected);
    const data = await (await api("/api/pronounce/reference", { method: "POST", body: fd })).json();
    $("pron-ref-audio").src = "data:audio/mp3;base64," + data.audio_b64;
    $("pron-ref-audio").play().catch(() => {});
    $("pron-status").textContent = "";
  } catch (e) {
    $("pron-status").textContent = "Audio unavailable: " + (e.message || e);
  }
});

// ---- Pass 2: record & score ----------------------------------------------- //
$("pron-record").addEventListener("click", async () => {
  if (!P.recording) {
    try {
      P.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      P.mr = new MediaRecorder(P.stream);
      P.chunks = [];
      P.mr.ondataavailable = (e) => e.data.size && P.chunks.push(e.data);
      P.mr.onstop = () => { P.stream.getTracks().forEach((t) => t.stop()); scoreTake(); };
      P.mr.start();
      P.recording = true;
      $("pron-record").textContent = "⏹ Stop";
      $("pron-record").classList.add("recording");
      $("pron-status").textContent = "recording… say your sentence, then Stop.";
    } catch (e) {
      $("pron-status").textContent = "mic error: " + (e.message || e);
    }
  } else {
    P.recording = false;
    $("pron-record").textContent = "● Record";
    $("pron-record").classList.remove("recording");
    if (P.mr && P.mr.state !== "inactive") P.mr.stop();
  }
});

// ---- Play back the learner's own last take (in-memory only — never uploaded) - //
$("pron-playback").addEventListener("click", () => {
  const a = $("pron-take-audio");
  if (a.src) { a.currentTime = 0; a.play(); }
});

async function scoreTake() {
  if (!P.chunks.length) { $("pron-status").textContent = "didn't catch that — record again"; return; }
  $("pron-status").textContent = "scoring…";
  const rawBlob = new Blob(P.chunks, { type: P.mr.mimeType || "audio/webm" });
  // Keep just the most recent take so the learner can replay their own voice and hear
  // the error. Held as an object URL in the browser only; nothing is saved server-side.
  if (P.takeUrl) URL.revokeObjectURL(P.takeUrl);
  P.takeUrl = URL.createObjectURL(rawBlob);
  $("pron-take-audio").src = P.takeUrl;
  $("pron-playback").hidden = false;
  try {
    const wav = await blobToWav(rawBlob);
    const fd = new FormData();
    fd.append("audio", wav, "take.wav");
    fd.append("target", P.corrected);
    const data = await (await api("/api/pronounce/assess", { method: "POST", body: fd })).json();
    if (!data.voiced) { $("pron-status").textContent = data.note || "no voice detected — record again"; return; }
    $("pron-score").textContent = `Score: ${data.overall_score}/100`;
    drawCurves($("pron-canvas"), data.learner_shape, data.target_shape);
    renderSyllables($("pron-result-syllables"), data.syllables);
    $("pron-note").textContent = data.note || "";
    renderLogged($("pron-logged"), data.logged);
    $("pron-results").hidden = false;
    $("pron-status").textContent = "record again to improve, or write a new sentence.";
  } catch (e) {
    $("pron-status").textContent = "error: " + (e.message || e);
  }
}
