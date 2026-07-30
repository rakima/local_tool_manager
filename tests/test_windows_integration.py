import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

import psutil
import pytest
from PySide6.QtWidgets import QApplication, QDialog

from local_tool_manager.models import Tool
from local_tool_manager.services import ProcessService
from local_tool_manager.ui.execution_tab import ExecutionTab
from local_tool_manager.ui.parameter_dialog import ParameterDialog


pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="Windowsのプロセス動作を検証するテスト"
)


def save_tool(repository, **values) -> Tool:
    defaults = {
        "name": "統合テスト",
        "entry_type": "command",
        "command": "cmd.exe",
    }
    return repository.create(Tool(**(defaults | values)))


def wait_until(predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.05)
    return False


def test_runs_windows_executable(repository):
    tool = save_tool(
        repository,
        command=str(Path(sys.executable).parent / "python.exe"),
        arguments='-c "raise SystemExit(0)"',
    )
    service = ProcessService(repository)

    process = service.start(tool)

    assert process.wait(timeout=5) == 0
    assert not service.is_running(tool.id)
    assert repository.list()[0].status == "completed"


def test_runs_python_script_with_spaced_argument_and_working_directory(
    repository, tmp_path
):
    working_directory = tmp_path / "working directory"
    working_directory.mkdir()
    script = working_directory / "script with spaces.py"
    output = working_directory / "result.txt"
    script.write_text(
        "import os, pathlib, sys\n"
        "pathlib.Path('result.txt').write_text("
        "sys.argv[1] + '\\n' + os.getcwd(), encoding='utf-8')\n",
        encoding="utf-8",
    )
    tool = save_tool(
        repository,
        command=str(script),
        arguments='"argument with spaces"',
        working_directory=str(working_directory),
    )
    service = ProcessService(repository)

    process = service.start(tool)

    assert process.wait(timeout=5) == 0
    assert not service.is_running(tool.id)
    argument, current_directory = output.read_text(encoding="utf-8").splitlines()
    assert argument == "argument with spaces"
    assert Path(current_directory) == working_directory


def test_restart_detection_and_child_process_stop(repository, tmp_path):
    child_pid_file = tmp_path / "child.pid"
    script = tmp_path / "parent.py"
    script.write_text(
        "import pathlib, subprocess, sys, time\n"
        "child = subprocess.Popen("
        "[sys.executable, '-c', 'import time; time.sleep(60)'])\n"
        f"pathlib.Path({str(child_pid_file)!r}).write_text(str(child.pid))\n"
        "time.sleep(60)\n",
        encoding="utf-8",
    )
    tool = save_tool(repository, command=str(script))
    first_service = ProcessService(repository)
    process = first_service.start(tool)

    try:
        assert wait_until(child_pid_file.exists)
        child_pid = int(child_pid_file.read_text())
        restarted_service = ProcessService(repository)
        assert restarted_service.is_running(tool.id)

        restarted_service.stop(tool.id)

        assert wait_until(lambda: not psutil.pid_exists(process.pid))
        assert wait_until(lambda: not psutil.pid_exists(child_pid))
        assert repository.list()[0].status == "stopped"
    finally:
        for pid in (process.pid, locals().get("child_pid")):
            if pid and psutil.pid_exists(pid):
                try:
                    psutil.Process(pid).kill()
                except psutil.NoSuchProcess:
                    pass


def test_url_parameter_dialog_passes_encoded_url_to_browser(repository):
    QApplication.instance() or QApplication([])
    tool = save_tool(
        repository,
        name="URL統合テスト",
        entry_type="url",
        command="",
        url="https://example.com/search?q={keyword}",
    )
    tab = ExecutionTab(repository, ProcessService(repository))
    tab.table.selectRow(0)

    with (
        patch.object(ParameterDialog, "exec", return_value=QDialog.DialogCode.Accepted),
        patch.object(ParameterDialog, "values", return_value={"keyword": "日本 語"}),
        patch("local_tool_manager.ui.execution_tab.webbrowser.open") as open_browser,
    ):
        open_browser.return_value = True
        tab.run_selected()

    open_browser.assert_called_once_with(
        "https://example.com/search?q=%E6%97%A5%E6%9C%AC+%E8%AA%9E"
    )
