"""Shared pytest fixtures for the WESPA API tests."""

from __future__ import annotations

import contextlib
import os
import sys
from pathlib import Path

import pymysql
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Use dedicated test database settings. Never let a developer's .env point the
# tests at production.
TEST_DB_HOST = os.environ.get("TEST_DB_HOST", "127.0.0.1")
TEST_DB_PORT = int(os.environ.get("TEST_DB_PORT", "3306"))
TEST_DB_USER = os.environ.get("TEST_DB_USER", "root")
TEST_DB_PASSWORD = os.environ.get("TEST_DB_PASSWORD", "root")
TEST_DB_NAME = os.environ.get("TEST_DB_NAME", "wespa_test")

if TEST_DB_NAME in {"wespa", "wespa_dev", "mysql", "information_schema", "performance_schema"}:
    raise RuntimeError(f"refusing to use protected database name: {TEST_DB_NAME}")

# Config is read at import time, so establish the test environment first.
os.environ["DB_HOST"] = TEST_DB_HOST
os.environ["DB_PORT"] = str(TEST_DB_PORT)
os.environ["DB_USER"] = TEST_DB_USER
os.environ["DB_PASSWORD"] = TEST_DB_PASSWORD
os.environ["DB_NAME"] = TEST_DB_NAME
os.environ["UPDATE_API_KEY"] = "test-api-key"
os.environ["CACHE_DEFAULT_TIMEOUT"] = "300"
os.environ["RATELIMIT_DEFAULT"] = "100000 per minute"

from tests.fixtures.seed import seed_database  # noqa: E402


def _connect(*, database: bool = True):
    kwargs = {
        "host": TEST_DB_HOST,
        "port": TEST_DB_PORT,
        "user": TEST_DB_USER,
        "password": TEST_DB_PASSWORD,
        "charset": "utf8mb4",
        "autocommit": True,
    }
    if database:
        kwargs["database"] = TEST_DB_NAME
    return pymysql.connect(**kwargs)


def _execute_script(conn, script: str) -> None:
    statements = [statement.strip() for statement in script.split(";") if statement.strip()]
    with conn.cursor() as cur:
        for statement in statements:
            cur.execute(statement)


@pytest.fixture(scope="session", autouse=True)
def test_database():
    """Create a clean test database and seed it once for the whole session."""
    admin = _connect(database=False)
    try:
        with admin.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS `{TEST_DB_NAME}`")
            cur.execute(f"CREATE DATABASE `{TEST_DB_NAME}` "
                        "CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
    finally:
        admin.close()

    schema_path = Path(__file__).parent / "fixtures" / "schema.sql"
    conn = _connect()
    try:
        _execute_script(conn, schema_path.read_text(encoding="utf-8"))
        world = seed_database(conn)
    finally:
        conn.close()
    return world


@pytest.fixture(scope="session")
def world(test_database):
    return test_database


@pytest.fixture(scope="session")
def app():
    from app import app as flask_app, limiter

    flask_app.config.update(TESTING=True)
    limiter.enabled = False
    return flask_app


@pytest.fixture()
def client(world, app):
    return app.test_client()


@pytest.fixture(scope="session")
def db():
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture()
def query_count(monkeypatch):
    """Count DB round trips made by the code under test.

    All query helpers ultimately use DatabasePool.get_connection, so this
    catches queries without changing production code.
    """
    from services import db as db_module

    counts = {"queries": 0}
    original = db_module.db_pool.get_connection

    @contextlib.contextmanager
    def counting_get_connection():
        counts["queries"] += 1
        with original() as conn:
            yield conn

    monkeypatch.setattr(db_module.db_pool, "get_connection", counting_get_connection)
    return counts
