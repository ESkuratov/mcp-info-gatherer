# syntax=docker/dockerfile:1

# ── Builder: ставим зависимости через uv ─────────────────────────
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
WORKDIR /app

# Сначала только манифесты — кэш слоя зависимостей
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --no-dev

# ── Runtime ──────────────────────────────────────────────────────
FROM python:3.12-slim
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY --from=builder /app/.venv ./.venv
COPY src ./src
COPY mcp_info_gatherer_server.py ./

# Рабочая директория для данных (Telethon session создаётся в CWD).
# Монтируется как volume в docker-compose — сессия переживает рестарты.
WORKDIR /data
VOLUME /data

EXPOSE 8002
CMD ["mcp-info-gatherer", "--transport", "sse", "--host", "0.0.0.0", "--port", "8002"]
