# Mandarin Coach — Chainlit agent app.
# uv-based build; dependencies cached separately from app code.
FROM python:3.12-slim

# uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    CHROMA_PATH=/var/data/chroma_db

# Install dependencies first (cached unless pyproject/uv.lock change).
# package = false in pyproject, so this installs deps only, no project build.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# App code + reference data
COPY app/ ./app/
COPY data/ ./data/

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

CMD ["chainlit", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
