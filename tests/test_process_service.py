from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from local_tool_manager.models import ExecutionHistory, Tool
from local_tool_manager.services.process_service import (
    ProcessService,
    build_command,
    resolve_python_executable,
)


def test_builds_command_without_splitting_quoted_argument():
    tool = Tool(
        name="test",
        entry_type="command",
        command=r"C:\Program Files\tool.exe",
        arguments='"C:\\input files\\sample.txt" --mode fast',
    )
    assert build_command(tool) == [
        r"C:\Program Files\tool.exe",
        r"C:\input files\sample.txt",
        "--mode",
        "fast",
    ]


def test_python_script_uses_current_interpreter():
    tool = Tool(
        name="python", entry_type="command", command=r"C:\tools\main.py", arguments="--x 1"
    )
    command = build_command(tool)
    assert Path(command[0]).name.lower().startswith("python")
    assert command[1:] == [r"C:\tools\main.py", "--x", "1"]


def test_relative_python_script_is_resolved_from_working_directory(tmp_path):
    script = tmp_path / "scripts" / "main.py"
    script.parent.mkdir()
    script.touch()
    tool = Tool(
        name="python",
        entry_type="command",
        working_directory=str(tmp_path),
        command=r"scripts\main.py",
    )

    command = build_command(tool)

    assert Path(command[0]).name.lower().startswith("python")
    assert Path(command[1]) == script


def test_frozen_app_uses_python_from_path(monkeypatch):
    monkeypatch.setattr(
        "local_tool_manager.services.process_service.sys.frozen", True, raising=False
    )

    with patch(
        "local_tool_manager.services.process_service.shutil.which",
        side_effect=lambda name: r"C:\Python314\python.exe"
        if name == "python.exe"
        else None,
    ):
        assert resolve_python_executable() == r"C:\Python314\python.exe"


def test_frozen_app_reports_missing_python(monkeypatch):
    monkeypatch.setattr(
        "local_tool_manager.services.process_service.sys.frozen", True, raising=False
    )

    with (
        patch("local_tool_manager.services.process_service.shutil.which", return_value=None),
        pytest.raises(RuntimeError, match="Python実行環境が見つかりません"),
    ):
        resolve_python_executable()


def test_nonexistent_pid_is_not_running_and_history_is_closed(repository):
    tool = repository.create(
        Tool(name="test", entry_type="command", command="python")
    )
    history_id = repository.create_history(
        ExecutionHistory(
            tool_id=tool.id,
            pid=99999999,
            process_create_time=1.0,
            started_at="2026-01-01T00:00:00+09:00",
            status="running",
        )
    )

    assert ProcessService(repository).is_running(tool.id) is False
    assert repository.latest_running_history(tool.id) is None


def test_same_pid_with_different_create_time_is_not_running(repository):
    tool = repository.create(
        Tool(name="test", entry_type="command", command="python")
    )
    repository.create_history(
        ExecutionHistory(
            tool_id=tool.id,
            pid=123,
            process_create_time=1.0,
            started_at="2026-01-01T00:00:00+09:00",
            status="running",
        )
    )
    process = Mock()
    process.create_time.return_value = 2.0
    process.is_running.return_value = True

    with patch("local_tool_manager.services.process_service.psutil.Process", return_value=process):
        assert ProcessService(repository).is_running(tool.id) is False

