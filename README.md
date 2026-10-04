# v2hub Telegram Bot

A Telegram bot for managing VPN subscriptions through the **v2hub** service. The bot's main
interface is a Mini App (control panel) launched directly from the chat.

### 🌐 Part of the [v2hub Ecosystem](https://github.com/nestthub/nestthub/blob/main/ecosystems/v2hub/README.md)

This package is one component of v2hub — see the full project overview, architecture, and all related repositories.

## Features

- Automatically issues an access token on first `/start` — no extra taps required
- Lets users view, refresh, and rotate their token (the old one is deactivated and the
  Mini App switches over automatically)
- Ships a Mini App launch button pre-authorized with the user's token
- Per-user rate limiting to protect the bot from spam/floods
- All v2hub data (tokens, provider ownership, authorizations) lives on the server and is
  always fetched fresh via the v2hub / v2hub-admin API — the bot's own database stores
  nothing about it. Locally it only keeps a Telegram `user_id` and the date it first
  started the bot.

## Requirements

- Python 3.11 or 3.12
- PostgreSQL (or Docker, see below)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Access credentials for the v2hub Admin API

## Getting Started

### With Docker (recommended)

```bash
cp .env.example .env
# fill in .env with your own values
docker compose up -d
```

### Without Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env
v2hub-bot
```

## Configuration

Settings are loaded from environment variables / `.env` via `pydantic-settings`.

| Variable           | Description                                                     |
| ------------------ | --------------------------------------------------------------- |
| `BOT_TOKEN`        | Telegram bot token                                              |
| `MINIAPP_URL`      | URL of the Mini App control panel                               |
| `SUPPORT_URL`      | Link shown on the "Contact support" button                      |
| `DATABASE_URL`     | Async SQLAlchemy database URL (e.g. `postgresql+asyncpg://...`) |
| `V2HUB_API_URL`    | Base URL of the v2hub Admin API                                 |
| `V2HUB_SECRET_KEY` | HMAC-SHA256 secret for the v2hub Admin API                      |

## Bot Commands

| Command     | Description                                    |
| ----------- | ---------------------------------------------- |
| `/start`    | Main menu; token is created automatically      |
| `/token`    | View, generate, or refresh your access token   |
| `/support`  | Contact support                                |
| `/help`     | Show help                                      |
| `/settings` | Bot settings, including the interface language |

## Project Structure

```
src/v2hub_bot/
├── main.py                  # Entry point: bot setup, middleware & router registration
├── config.py                 # Settings loaded from .env (pydantic-settings)
├── locales/
│   ├── i18n.py                # gettext translator lookup (falls back to English)
│   ├── compile_locales.py       # Pure-Python .po -> .mo compiler (run by the Docker entrypoint)
│   └── {en,ru,fa,zh}/         # User-facing texts and button labels (.po sources)
├── db/
│   ├── engine.py              # Async SQLAlchemy engine, session factory
│   ├── models.py               # ORM models (User.id + lang + created_at + is_banned)
│   └── crud.py                  # CRUD helpers (users by Telegram id, interface language)
├── handlers/
│   ├── start.py                 # /start — main menu + automatic token creation
│   ├── token.py                  # /token — view/generate/refresh token
│   ├── settings.py                 # /settings — interface language selection
│   ├── support.py                  # /support
│   └── help.py                       # /help
├── services/
│   ├── v2hub.py                       # Facade over the v2hub-admin client (AsyncAdminClient)
│   ├── users.py                         # Local user lookup + translator for an incoming event
│   └── keyboards.py                     # Inline keyboard factories, Mini App token passing
└── middlewares/
    └── throttle.py                        # Per-user rate limiting

tests/
├── conftest.py               # Shared fixtures: in-memory SQLite session, env defaults
├── helpers.py                 # Shared test data/factories: translator, Telegram mocks
├── test_config.py             # Settings validation
├── test_models.py               # ORM model behavior
├── test_crud.py                   # Database CRUD helpers
├── test_v2hub_service.py             # v2hub Admin API facade
├── test_keyboards.py                    # Inline keyboard construction
├── test_throttle_middleware.py             # Rate-limiting middleware
├── test_handlers_start.py                    # /start and menu callback
├── test_handlers_token.py                       # /token and its callbacks
├── test_handlers_support_help.py                    # /support and /help
├── test_handlers_settings.py                          # /settings and language selection
├── test_users_service.py                                # Local user + translator lookup
├── test_i18n.py                                           # Translators, language normalisation, catalog consistency
├── test_compile_locales.py                                  # Pure-Python .po -> .mo compiler
├── test_docker_entrypoint.py                                  # Entrypoint compiles translations before start
└── test_migrations.py                                           # Alembic migrations
```

## Development

Install with development dependencies:

```bash
pip install -e ".[dev]"
```

### Translations

Texts live in `src/v2hub_bot/locales/<lang>/LC_MESSAGES/messages.po`. The compiled `.mo`
files are git-ignored build artifacts and must be generated before running the application or tests.

- **Running locally without Docker:** `python -m v2hub_bot.locales.compile_locales`
- **Before running tests:** `python -m v2hub_bot.locales.compile_locales`

### Running tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=v2hub_bot --cov-report=term-missing
```

Tests are organized by target module and grouped with `unit` / `integration` / `slow`
markers (see `pyproject.toml`). Database-touching tests use an isolated in-memory SQLite
session per test, so no external services are required to run the suite.

### Linting & type checking

```bash
ruff check src/
mypy src/
```

### Pre-commit hooks

```bash
pre-commit install
```

## License

MIT — see [LICENSE](LICENSE).
