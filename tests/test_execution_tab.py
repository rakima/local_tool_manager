from datetime import datetime
from unittest.mock import Mock

from local_tool_manager.models import Tool
from local_tool_manager.ui.execution_tab import ExecutionTab
from local_tool_manager.ui.execution_tab import format_last_run_at


def test_formats_last_run_at_for_display():
    value = datetime.now().astimezone().replace(
        year=2026, month=8, day=4, hour=5, minute=48, second=29, microsecond=0
    )

    assert format_last_run_at(value.isoformat()) == "2026/08/04 05:48:29"


def test_formats_empty_last_run_at_as_blank():
    assert format_last_run_at(None) == ""
    assert format_last_run_at("") == ""


def test_keeps_invalid_last_run_at_value():
    assert format_last_run_at("invalid") == "invalid"


def test_edit_button_opens_selected_tool(repository):
    tool = repository.create(
        Tool(name="編集対象", entry_type="command", command="python")
    )
    tab = ExecutionTab(repository, Mock())
    requested = []
    tab.edit_requested.connect(lambda selected, duplicate: requested.append(
        (selected, duplicate)
    ))

    assert not tab.edit_button.isEnabled()

    tab.table.selectRow(0)
    tab.edit_button.click()

    assert tab.edit_button.isEnabled()
    assert requested == [(tool, False)]
