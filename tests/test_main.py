from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from v2hub_bot import main as main_module

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_main_starts_polling_with_all_routers() -> None:
    """Schema setup is Alembic's responsibility now, run separately before
    the bot starts — main() no longer touches the database on startup."""
    with (
        patch.object(main_module, "Bot") as bot_cls,
        patch.object(main_module, "Dispatcher") as dispatcher_cls,
    ):
        dp = dispatcher_cls.return_value
        dp.resolve_used_update_types.return_value = ["message", "callback_query"]
        dp.start_polling = AsyncMock()

        await main_module.main()

    bot_cls.assert_called_once()
    assert dp.include_router.call_count == 6
    dp.start_polling.assert_awaited_once()


def test_cli_runs_main_via_asyncio() -> None:
    with patch.object(main_module.asyncio, "run") as run_mock:
        main_module.cli()

    run_mock.assert_called_once()
    # asyncio.run is mocked out, so the coroutine it was given is never
    # awaited by the real event loop — close it explicitly to avoid a
    # "coroutine was never awaited" warning leaking into other tests.
    passed_coroutine = run_mock.call_args.args[0]
    passed_coroutine.close()
