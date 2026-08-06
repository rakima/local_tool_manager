from local_tool_manager.database import Database, ToolRepository
from local_tool_manager.database.migrations import initialize_database


def test_adds_sort_order_to_existing_database(tmp_path):
    database = Database(tmp_path / "legacy.db")
    with database.connect() as connection:
        connection.executescript(
            """
            CREATE TABLE tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                entry_type TEXT NOT NULL,
                working_directory TEXT,
                command TEXT,
                arguments TEXT,
                url TEXT,
                allow_multiple_instances INTEGER NOT NULL DEFAULT 0,
                show_console INTEGER NOT NULL DEFAULT 0,
                is_favorite INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            INSERT INTO tools (
                name, entry_type, command, is_favorite, created_at, updated_at
            ) VALUES
                ('Beta', 'command', 'python', 0, '', ''),
                ('Alpha', 'command', 'python', 1, '', ''),
                ('Gamma', 'command', 'python', 0, '', '');
            """
        )

    initialize_database(database)

    assert [tool.name for tool in ToolRepository(database).list()] == [
        "Alpha",
        "Beta",
        "Gamma",
    ]
