import sqlite3

import pytest

from local_tool_manager.database import Database


def test_connection_is_closed_after_success(tmp_path):
    database = Database(tmp_path / "test.db")

    with database.connect() as connection:
        connection.execute("CREATE TABLE sample (id INTEGER)")

    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")


def test_connection_rolls_back_and_closes_after_failure(tmp_path):
    database = Database(tmp_path / "test.db")

    with database.connect() as connection:
        connection.execute("CREATE TABLE sample (id INTEGER)")

    with pytest.raises(RuntimeError):
        with database.connect() as failed_connection:
            failed_connection.execute("INSERT INTO sample VALUES (1)")
            raise RuntimeError("失敗")

    with pytest.raises(sqlite3.ProgrammingError):
        failed_connection.execute("SELECT 1")

    with database.connect() as connection:
        count = connection.execute("SELECT count(*) FROM sample").fetchone()[0]

    assert count == 0
