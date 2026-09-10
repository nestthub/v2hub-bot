from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_package_imports_cleanly() -> None:
    import v2hub_bot  # noqa: F401


def test_main_module_registers_all_routers() -> None:
    from v2hub_bot.handlers import (
        help_router,
        provider_router,
        start_router,
        support_router,
        token_router,
    )

    assert help_router is not None
    assert provider_router is not None
    assert start_router is not None
    assert support_router is not None
    assert token_router is not None


def test_db_package_exports_only_local_user_helpers() -> None:
    """The db package must no longer expose provider/token persistence helpers —
    that data lives entirely on the v2hub server now. It also no longer
    exposes init_db: schema management moved to Alembic migrations."""
    from v2hub_bot.db import async_session, get_or_create_user, get_session, get_user

    assert callable(get_or_create_user)
    assert callable(get_user)
    assert async_session is not None
    assert callable(get_session)

    import v2hub_bot.db as db_module

    forbidden = {
        "init_db",
        "save_token",
        "create_provider",
        "update_provider",
        "delete_provider",
        "get_provider_by_name",
        "get_provider_by_owner_id",
    }
    assert forbidden.isdisjoint(dir(db_module))


def test_services_package_exports_expected_symbols() -> None:
    from v2hub_bot.services import v2hub_client, v2hubError

    assert v2hub_client is not None
    assert issubclass(v2hubError, Exception)


def test_v2hub_service_exposes_provider_ownership_lookup() -> None:
    """get_provider_by_owner_id replaces the old local Provider table lookup."""
    from v2hub_bot.services.v2hub import v2hubService

    assert hasattr(v2hubService, "get_provider_by_owner_id")
