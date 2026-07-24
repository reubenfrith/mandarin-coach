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

from langchain_litellm import ChatLiteLLM

# Route LangSmith traces to a named project instead of "default". setdefault so an
# explicit env var (or the eval harness, which sets its own) still wins. config is
# imported by every app module, so this runs before the first traced LLM call.
os.environ.setdefault("LANGSMITH_PROJECT", "mandarin-coach")

# The three Chinese-native candidates for the Task 6 model bake-off.
# Keys are the short names used everywhere else in the app / eval harness.
MODELS = {
    "deepseek": "openrouter/deepseek/deepseek-v4-flash",
    "glm": "openrouter/z-ai/glm-5.2",
    "qwen": "openrouter/qwen/qwen3.5-397b-a17b",
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
# Voice Conversation Partner — OpenRouter audio pipeline.
# OpenRouter has no speech-to-speech realtime API, so voice is a turn-based
# pipeline on the SAME OPENROUTER_API_KEY as the text brain: STT (transcribe the
# learner) -> chat LLM (converse) -> TTS (speak the reply). All three go through
# OpenRouter's OpenAI-compatible audio endpoints. Slugs are overridable; if a slug
# is rejected, correct it against https://openrouter.ai/models .
# --------------------------------------------------------------------------- #
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
# The conversation LLM is a MODELS key (see above). glm is fast and non-hanging —
# the right default for a live back-and-forth (deepseek, a reasoning model, stalls).
CONVERSATION_MODEL = os.environ.get("CONVERSATION_MODEL", "glm")
STT_MODEL = os.environ.get("STT_MODEL", "openai/gpt-4o-mini-transcribe")
TTS_MODEL = os.environ.get("TTS_MODEL", "openai/gpt-4o-mini-tts")
TTS_VOICE = os.environ.get("TTS_VOICE", "alloy")


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
