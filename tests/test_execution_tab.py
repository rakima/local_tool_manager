from datetime import datetime

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
