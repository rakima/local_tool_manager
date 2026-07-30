import pytest

from local_tool_manager.database import Database, ToolRepository
from local_tool_manager.database.migrations import initialize_database


@pytest.fixture
def repository(tmp_path):
    database = Database(tmp_path / "test.db")
    initialize_database(database)
    return ToolRepository(database)

