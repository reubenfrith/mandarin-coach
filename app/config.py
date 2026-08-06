"""LiteLLM + OpenRouter model configuration.

All LLM calls route through OpenRouter under a single OPENROUTER_API_KEY. Each
model is wrapped as a ChatLiteLLM instance so that calls are LangChain runnables
and are captured automatically by LangSmith tracing (rather than being invisible
direct litellm calls).

Model slugs are current as of July 2026. If OpenRouter rejects a slug on first
run, its error lists the valid names — correct the MODELS dict here against
https://openrouter.ai/models .
"""
import os

import litellm
from langchain_litellm import ChatLiteLLM

# Silence litellm's "Provider List: …" / "Give Feedback" footers. It prints them during
# its internal cost/token lookup whenever a slug isn't in its built-in cost map — which is
# every call here, since our OpenRouter slugs are newer than litellm's map. The actual
# completions succeed; these lines are pure noise. This suppresses only those hints, not
# real error tracebacks.
litellm.suppress_debug_info = True

# Route LangSmith traces to a named project instead of "default". setdefault so an
# explicit env var (or the eval harness, which sets its own) still wins. config is
# imported by every app module, so this runs before the first traced LLM call.
os.environ.setdefault("LANGSMITH_PROJECT", "mandarin-coach")

# The three Chinese-native candidates for the Task 6 model bake-off (the TEXT coach).
# Keys are the short names used everywhere else in the app / eval harness.
# gpt-4o-mini is the odd one out: it routes DIRECT to OpenAI (not OpenRouter) and is
# the low-latency, NON-reasoning model the voice paths use — a live spoken turn can't
# afford the ~5s reasoning trace glm/deepseek emit before every reply.
MODELS = {
    "deepseek": "openrouter/deepseek/deepseek-v4-flash",
    "glm": "openrouter/z-ai/glm-5.2",
    "qwen": "openrouter/qwen/qwen3.5-397b-a17b",
    "gpt-4o-mini": "openai/gpt-4o-mini",
    # Direct-OpenAI, stronger than gpt-4o-mini. Not used by any live coach path — it's here
    # as an INDEPENDENT eval judge (a stronger, different model grading the gpt-4o-mini coach,
    # so a same-model self-preference can't inflate a surface's scores).
    "gpt-4o": "openai/gpt-4o",
    # Frontier EVAL-ONLY judges (no live coach path uses them). Routed via OpenRouter because the
    # direct-OpenAI gpt-5/o-series reject temperature=0 (needed for reproducible judging); the
    # OpenRouter route accepts it. Both are cross-provider from the deepseek coach, so no
    # self-preference. Used to test whether a stronger judge closes the secondary-error gaps
    # (see evals/notes/teaching-quality-findings.md).
    "claude-opus": "openrouter/anthropic/claude-opus-4.8",
    "gpt-5": "openrouter/openai/gpt-5",
}

DEFAULT_MODEL = "deepseek"
# Fast, reliable non-reasoning model used as the fallback when the primary stalls
# or errors (see agent.run_agent). deepseek is a reasoning model and occasionally
# hangs many minutes on OpenRouter, so we need a guaranteed escape hatch.
FALLBACK_MODEL = "glm"
# Per-call ceiling handed to litellm (best-effort — litellm does not always honour
# it on a hung streaming connection, which is why agent.run_agent ALSO wraps the
# whole turn in an asyncio.wait_for hard timeout).
REQUEST_TIMEOUT = float(os.environ.get("REQUEST_TIMEOUT", "90"))

# --------------------------------------------------------------------------- #
# Voice pipeline — all-OpenAI, turn-based (no speech-to-speech realtime API).
# One spoken turn is STT (transcribe) -> chat LLM (converse) -> TTS (speak). Every leg
# runs DIRECT on OPENAI_API_KEY to keep voice on one fast provider with no proxy hop —
# the OpenRouter hop plus a reasoning chat model (glm/deepseek) made live turns sluggish.
# NOTE: OpenRouter has SINCE added an OpenAI-compatible TTS route (POST /audio/speech,
# streaming, same SDK call we use) and an STT route (though its /audio/transcriptions
# takes base64 input_audio, not the SDK's multipart file — not a drop-in). So direct-
# OpenAI is now a LATENCY preference, not a hard requirement: a future fallback provider
# could route voice through OpenRouter. The TEXT coach still uses the OpenRouter models above.
# --------------------------------------------------------------------------- #
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
# The voice conversation/coach LLM is a MODELS key. gpt-4o-mini is fast and NON-reasoning
# — the right default for a live back-and-forth (glm/deepseek emit a ~5s reasoning trace
# before each reply). Routes direct to OpenAI (see the MODELS note above).
CONVERSATION_MODEL = os.environ.get("CONVERSATION_MODEL", "gpt-4o-mini")
# STT goes DIRECT to OpenAI (OPENAI_API_KEY), using OpenAI's native, unprefixed model
# name — one fast provider, no proxy hop (see the pipeline note above).
STT_MODEL = os.environ.get("STT_MODEL", "gpt-4o-mini-transcribe")
# Voice-coach STT language hint. Empty/unset => auto-detect (omit the hint), so a spoken
# English clarifying question ("why is that wrong?") transcribes AS English instead of
# being mangled into Chinese phonetics — the routing signal the voice coach needs. Pass-1
# pronunciation drafts stay pinned to zh (they're always Chinese). Set to an ISO-639-1
# code (e.g. "zh") to force a language.
VOICE_STT_LANGUAGE = os.environ.get("VOICE_STT_LANGUAGE") or None
TTS_MODEL = os.environ.get("TTS_MODEL", "gpt-4o-mini-tts")
TTS_VOICE = os.environ.get("TTS_VOICE", "alloy")


def openai_key() -> str:
    """OpenAI key for the direct-OpenAI voice pipeline (STT + TTS)."""
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key or key.startswith("#"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set (required for the direct-OpenAI voice "
            "pipeline — STT and TTS)."
        )
    return key


def openrouter_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key or key.startswith("#"):
        raise RuntimeError("OPENROUTER_API_KEY is not set (required for the voice pipeline).")
    return key


def get_llm(
    model_key: str = DEFAULT_MODEL,
    *,
    temperature: float = 0.2,
    streaming: bool = True,
    timeout: float = REQUEST_TIMEOUT,
) -> ChatLiteLLM:
    """Return a ChatLiteLLM bound to one of the candidate models.

    `model_key` is a short name from MODELS ("deepseek" / "glm" / "qwen"), which
    lets the eval harness swap models by key without touching the rest of the app.
    `timeout` caps each request so a stalled provider can't hang a call forever.
    """
    if model_key not in MODELS:
        raise ValueError(
            f"Unknown model '{model_key}'. Choose from {list(MODELS)}."
        )
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Copy .env.example to .env and fill it in."
        )
    return ChatLiteLLM(
        model=MODELS[model_key],
        temperature=temperature,
        streaming=streaming,
        request_timeout=timeout,
    )
