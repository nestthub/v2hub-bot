FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./

COPY alembic.ini ./
COPY alembic ./alembic

RUN pip install --no-cache-dir uv

COPY src ./src

# Translations: compile .po -> .mo (git-ignored build artifacts). gettext is
# only needed for msgfmt, so it is removed again in the same layer.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gettext \
    && python src/v2hub_bot/locales/compile_locales.py \
    && apt-get purge -y --auto-remove gettext \
    && rm -rf /var/lib/apt/lists/*

RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

CMD ["v2hub-bot"]
