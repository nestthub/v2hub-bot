from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text

if TYPE_CHECKING:
    from types import ModuleType

pytestmark = pytest.mark.unit

VERSIONS_DIR = Path(__file__).parent.parent / "alembic" / "versions"


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, VERSIONS_DIR / f"{name}.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_chain_is_linear_and_ends_at_latest() -> None:
    revisions = {}
    for path in sorted(VERSIONS_DIR.glob("0*.py")):
        module = _load(path.stem)
        revisions[module.revision] = module.down_revision

    assert revisions == {"0001": None, "0002": "0001", "0003": "0002"}


def test_0003_adds_lang_with_default_for_existing_rows_and_downgrades() -> None:
    migration = _load("0003_add_user_lang")
    engine = create_engine("sqlite://")

    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE users (id BIGINT PRIMARY KEY, is_banned BOOLEAN NOT NULL)"))
        conn.execute(text("INSERT INTO users (id, is_banned) VALUES (1, 0)"))

        with Operations.context(MigrationContext.configure(conn)):
            migration.upgrade()

        columns = {c["name"]: c for c in inspect(conn).get_columns("users")}
        assert "lang" in columns
        assert columns["lang"]["nullable"] is False
        # Pre-existing users get the default language instead of NULL.
        assert conn.execute(text("SELECT lang FROM users WHERE id = 1")).scalar_one() == "en"

        with Operations.context(MigrationContext.configure(conn)):
            migration.downgrade()

        assert "lang" not in {c["name"] for c in inspect(conn).get_columns("users")}
