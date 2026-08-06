from __future__ import annotations

import logging

from .connection import Database


SCHEMA = """
CREATE TABLE IF NOT EXISTS tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    entry_type TEXT NOT NULL CHECK(entry_type IN ('command', 'url')),
    working_directory TEXT,
    command TEXT,
    arguments TEXT,
    url TEXT,
    allow_multiple_instances INTEGER NOT NULL DEFAULT 0,
    show_console INTEGER NOT NULL DEFAULT 0,
    is_favorite INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS execution_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL,
    pid INTEGER,
    process_create_time REAL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    exit_code INTEGER,
    status TEXT NOT NULL CHECK(status IN ('running', 'completed', 'failed', 'stopped')),
    FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_history_tool_started
ON execution_history(tool_id, started_at DESC);
"""


def initialize_database(database: Database) -> None:
    with database.connect() as connection:
        connection.executescript(SCHEMA)
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(tools)")
        }
        if "sort_order" not in columns:
            connection.execute(
                "ALTER TABLE tools ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0"
            )
            rows = connection.execute(
                "SELECT id FROM tools "
                "ORDER BY is_favorite DESC, lower(name), id"
            ).fetchall()
            for sort_order, row in enumerate(rows):
                connection.execute(
                    "UPDATE tools SET sort_order=? WHERE id=?",
                    (sort_order, row["id"]),
                )
    logging.getLogger(__name__).info("DB初期化: %s", database.path)

