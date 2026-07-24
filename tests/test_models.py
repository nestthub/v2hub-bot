from __future__ import annotations

import pytest

from v2hub_bot.db.models import User

pytestmark = pytest.mark.unit


def test_user_repr_contains_id() -> None:
    user = User(id=123)

    assert repr(user) == "<User id=123>"


def test_user_defaults_before_flush() -> None:
    user = User(id=1)

    assert user.api_token is None
    assert user.token_generated_at is None
