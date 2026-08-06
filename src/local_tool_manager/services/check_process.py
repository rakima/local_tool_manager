from __future__ import annotations

import locale

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from local_tool_manager.models import Tool

from .process_service import build_command, resolve_working_directory


def decode_process_output(data: bytes) -> str:
    encodings = ("utf-8", locale.getpreferredencoding(False))
    for encoding in dict.fromkeys(encodings):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


class CheckProcessRunner(QObject):
    standard_output = Signal(str)
    standard_error = Signal(str)
    running_changed = Signal(bool)
    finished = Signal(int)
    failed = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        self.process.started.connect(lambda: self.running_changed.emit(True))
        self.process.readyReadStandardOutput.connect(self._read_stdout)
        self.process.readyReadStandardError.connect(self._read_stderr)
        self.process.finished.connect(self._on_finished)
        self.process.errorOccurred.connect(self._on_error)

    @property
    def is_running(self) -> bool:
        return self.process.state() != QProcess.ProcessState.NotRunning

    def start(self, tool: Tool) -> list[str]:
        if self.is_running:
            raise RuntimeError("実行チェックはすでに実行中です。")
        command = build_command(tool)
        working_directory = resolve_working_directory(tool)
        if working_directory:
            self.process.setWorkingDirectory(working_directory)
        else:
            self.process.setWorkingDirectory("")
        self.process.start(command[0], command[1:])
        return command

    def stop(self) -> None:
        if not self.is_running:
            return
        self.process.terminate()
        QTimer.singleShot(3000, self._kill_if_running)

    def shutdown(self) -> None:
        if self.is_running:
            self.process.kill()
            self.process.waitForFinished(1000)
        self.process.close()

    def _kill_if_running(self) -> None:
        if self.is_running:
            self.process.kill()

    def _read_stdout(self) -> None:
        data = bytes(self.process.readAllStandardOutput())
        if data:
            self.standard_output.emit(decode_process_output(data))

    def _read_stderr(self) -> None:
        data = bytes(self.process.readAllStandardError())
        if data:
            self.standard_error.emit(decode_process_output(data))

    def _on_finished(self, exit_code: int, _exit_status) -> None:
        self._read_stdout()
        self._read_stderr()
        self.running_changed.emit(False)
        self.finished.emit(exit_code)

    def _on_error(self, error: QProcess.ProcessError) -> None:
        if error != QProcess.ProcessError.FailedToStart:
            return
        self.running_changed.emit(False)
        self.failed.emit(self.process.errorString())
