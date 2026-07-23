# V2Hub Telegram Bot

A Telegram bot for managing VPN subscriptions through the **V2Hub** service. The bot's main
interface is a Mini App (control panel) launched directly from the chat.

## Features

- Automatically issues an access token on first `/start` — no extra taps required
- Lets users view, refresh, and rotate their token (the old one is deactivated and the
  Mini App switches over automatically)
- Ships a Mini App launch button pre-authorized with the user's token
- Per-user rate limiting to protect the bot from spam/floods
- Async PostgreSQL storage (SQLAlchemy + asyncpg) for the Telegram ↔ V2Hub account link

## Requirements

- Python 3.11 or 3.12
- PostgreSQL (or Docker, see below)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Access credentials for the V2Hub Admin API

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
| `V2HUB_API_URL`    | Base URL of the V2Hub Admin API                                 |
| `V2HUB_SECRET_KEY` | HMAC-SHA256 secret for the V2Hub Admin API                      |

## Bot Commands

| Command    | Description                                  |
| ---------- | -------------------------------------------- |
| `/start`   | Main menu; token is created automatically    |
| `/token`   | View, generate, or refresh your access token |
| `/support` | Contact support                              |
| `/help`    | Show help                                    |

## Project Structure

```
src/v2hub_bot/
├── main.py                  # Entry point: bot setup, middleware & router registration
├── config.py                 # Settings loaded from .env (pydantic-settings)
├── locales/
│   └── ru.py                 # User-facing text and button labels (Russian)
├── db/
│   ├── engine.py              # Async SQLAlchemy engine, session factory, init_db
│   ├── models.py               # ORM models
│   └── crud.py                  # CRUD helpers
├── handlers/
│   ├── start.py                 # /start — main menu + automatic token creation
│   ├── token.py                  # /token — view/generate/refresh token
│   ├── support.py                  # /support
│   └── help.py                       # /help
├── services/
│   ├── v2hub.py                       # Facade over the v2hub-admin client (AsyncAdminClient)
│   └── keyboards.py                     # Inline keyboard factories, Mini App token passing
└── middlewares/
    └── throttle.py                        # Per-user rate limiting

tests/
├── conftest.py               # Shared fixtures: in-memory SQLite session, env defaults
├── test_config.py             # Settings validation
├── test_models.py               # ORM model behavior
├── test_crud.py                   # Database CRUD helpers
├── test_v2hub_service.py             # V2Hub Admin API facade
├── test_keyboards.py                    # Inline keyboard construction
├── test_throttle_middleware.py             # Rate-limiting middleware
├── test_handlers_start.py                    # /start and menu callback
├── test_handlers_token.py                       # /token and its callbacks
└── test_handlers_support_help.py                    # /support and /help
```

## Development

Install with development dependencies:

```bash
pip install -e ".[dev]"
```

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
