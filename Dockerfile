FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./

RUN pip install --no-cache-dir uv

COPY src ./src

RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

CMD ["v2hub-bot"]
