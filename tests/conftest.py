import os

import pytest
from PySide6.QtWidgets import QApplication

from local_tool_manager.database import Database, ToolRepository
from local_tool_manager.database.migrations import initialize_database


@pytest.fixture(scope="session", autouse=True)
def qt_application():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    application = QApplication.instance() or QApplication([])
    yield application


@pytest.fixture
def repository(tmp_path):
    database = Database(tmp_path / "test.db")
    initialize_database(database)
    return ToolRepository(database)

