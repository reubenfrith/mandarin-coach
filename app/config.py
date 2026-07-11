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

# The three Chinese-native candidates for the Task 6 model bake-off.
# Keys are the short names used everywhere else in the app / eval harness.
MODELS = {
    "deepseek": "openrouter/deepseek/deepseek-v4-flash",
    "glm": "openrouter/z-ai/glm-5.2",
    "qwen": "openrouter/qwen/qwen3.5-397b-a17b",
}

DEFAULT_MODEL = "deepseek"


def get_llm(
    model_key: str = DEFAULT_MODEL,
    *,
    temperature: float = 0.2,
    streaming: bool = True,
) -> ChatLiteLLM:
    """Return a ChatLiteLLM bound to one of the candidate models.

    `model_key` is a short name from MODELS ("deepseek" / "glm" / "qwen"), which
    lets the eval harness swap models by key without touching the rest of the app.
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
    )
