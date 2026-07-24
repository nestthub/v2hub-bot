from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_package_imports_cleanly() -> None:
    import v2hub_bot  # noqa: F401


def test_main_module_registers_all_routers() -> None:
    from v2hub_bot.handlers import help_router, start_router, support_router, token_router

    assert help_router is not None
    assert start_router is not None
    assert support_router is not None
    assert token_router is not None


def test_db_package_exports_expected_symbols() -> None:
    from v2hub_bot.db import (
        async_session,
        get_or_create_user,
        get_session,
        get_user,
        init_db,
        save_token,
    )

    assert callable(get_or_create_user)
    assert callable(get_user)
    assert callable(save_token)
    assert callable(init_db)
    assert async_session is not None
    assert callable(get_session)


def test_services_package_exports_expected_symbols() -> None:
    from v2hub_bot.services import V2HubError, v2hub_client

    assert v2hub_client is not None
    assert issubclass(V2HubError, Exception)
