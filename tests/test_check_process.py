import sys
import time

from local_tool_manager.models import Tool
from local_tool_manager.services.check_process import (
    CheckProcessRunner,
    decode_process_output,
)


def wait_until(qt_application, predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qt_application.processEvents()
        if predicate():
            return True
        time.sleep(0.01)
    return False


def test_decodes_utf8_process_output():
    assert decode_process_output("日本語".encode()) == "日本語"


def test_runs_command_asynchronously_and_collects_output(qt_application):
    runner = CheckProcessRunner()
    stdout = []
    stderr = []
    exit_codes = []
    runner.standard_output.connect(stdout.append)
    runner.standard_error.connect(stderr.append)
    runner.finished.connect(exit_codes.append)
    tool = Tool(
        name="check",
        entry_type="command",
        command=sys.executable,
        arguments='-c "import sys; print(\'output\'); print(\'error\', file=sys.stderr)"',
    )

    command = runner.start(tool)

    assert command[0] == sys.executable
    assert wait_until(qt_application, lambda: bool(exit_codes))
    assert exit_codes == [0]
    assert "output" in "".join(stdout)
    assert "error" in "".join(stderr)
    runner.shutdown()
