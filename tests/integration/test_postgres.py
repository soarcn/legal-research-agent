"""Opt-in checks against the project's local PostgreSQL container."""

from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import URL, make_url

from legal_research.adapters.postgres.connection import AsyncPostgresDatabase
from legal_research.config import get_settings

pytestmark = pytest.mark.real_service


@pytest.mark.asyncio
async def test_async_postgres_adapter_proves_connection_commit_and_rollback() -> None:
    database = AsyncPostgresDatabase(get_settings().database_url)

    try:
        await database.ping()

        async with database.engine.connect() as connection:
            await connection.execute(
                text(
                    "CREATE TEMPORARY TABLE p1_transaction_probe "
                    "(value TEXT NOT NULL) ON COMMIT PRESERVE ROWS"
                )
            )
            await connection.commit()

            async with connection.begin():
                await connection.execute(
                    text("INSERT INTO p1_transaction_probe (value) VALUES ('committed')")
                )

            committed_count = await connection.scalar(
                text("SELECT count(*) FROM p1_transaction_probe")
            )
            assert committed_count == 1

            rollback_transaction = await connection.begin()
            await connection.execute(
                text("INSERT INTO p1_transaction_probe (value) VALUES ('rolled back')")
            )
            await rollback_transaction.rollback()

            rolled_back_count = await connection.scalar(
                text("SELECT count(*) FROM p1_transaction_probe")
            )
            assert rolled_back_count == 1
    finally:
        await database.dispose()


@pytest.mark.asyncio
async def test_empty_alembic_baseline_creates_no_legal_domain_tables() -> None:
    source_url = make_url(get_settings().database_url)
    baseline_database_name = f"p1_baseline_{uuid4().hex}"
    baseline_url = source_url.set(database=baseline_database_name)
    admin_url = source_url.set(database="postgres")
    admin_database = AsyncPostgresDatabase(str(admin_url))
    baseline_database: AsyncPostgresDatabase | None = None

    try:
        async with admin_database.engine.connect() as connection:
            autocommit_connection = await connection.execution_options(isolation_level="AUTOCOMMIT")
            await autocommit_connection.execute(text(f'CREATE DATABASE "{baseline_database_name}"'))

        config = Config("alembic.ini")
        config.attributes["database_url"] = _sync_url(baseline_url)
        command.upgrade(config, "head")

        baseline_database = AsyncPostgresDatabase(str(baseline_url))
        async with baseline_database.engine.connect() as connection:
            result = await connection.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
            tables = set(result.scalars())
    finally:
        if baseline_database is not None:
            await baseline_database.dispose()

        async with admin_database.engine.connect() as connection:
            autocommit_connection = await connection.execution_options(isolation_level="AUTOCOMMIT")
            await autocommit_connection.execute(
                text(f'DROP DATABASE IF EXISTS "{baseline_database_name}" WITH (FORCE)')
            )
        await admin_database.dispose()

    assert tables == {"alembic_version"}


def _sync_url(database_url: URL) -> str:
    """Return the synchronous URL required by Alembic's migration environment."""

    return str(database_url.set(drivername="postgresql+psycopg"))
