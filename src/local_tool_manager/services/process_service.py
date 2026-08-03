from __future__ import annotations

import logging
import os
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable

import psutil

from local_tool_manager.database import ToolRepository
from local_tool_manager.models import ExecutionHistory, Tool


class AlreadyRunningError(RuntimeError):
    pass


def build_command(tool: Tool) -> list[str]:
    command = resolve_command(tool)
    arguments = shlex.split(tool.arguments, posix=False) if tool.arguments.strip() else []
    arguments = [part.strip('"') for part in arguments]
    if Path(command).suffix.lower() == ".py":
        return [sys.executable, command, *arguments]
    return [command, *arguments]


def resolve_command(tool: Tool) -> str:
    command = os.path.expandvars(tool.command.strip().strip('"'))
    command_path = Path(command)
    working_directory = os.path.expandvars(tool.working_directory.strip())
    relative_path = Path(working_directory) / command_path
    if (
        not command_path.is_absolute()
        and working_directory
        and (
            relative_path.is_file()
            or any(separator in command for separator in "\\/")
        )
    ):
        return str(relative_path.resolve())
    return command


def resolve_working_directory(tool: Tool) -> str | None:
    if tool.working_directory.strip():
        return os.path.expandvars(tool.working_directory.strip())
    command = Path(os.path.expandvars(tool.command.strip().strip('"')))
    return str(command.parent) if command.is_absolute() else None


class ProcessService:
    def __init__(
        self,
        repository: ToolRepository,
        process_factory: Callable[..., subprocess.Popen] = subprocess.Popen,
    ) -> None:
        self.repository = repository
        self.process_factory = process_factory
        self.logger = logging.getLogger(__name__)
        self._active_processes: dict[int, tuple[subprocess.Popen, int]] = {}

    def is_running(self, tool_id: int) -> bool:
        active = self._active_processes.get(tool_id)
        if active is not None:
            process, history_id = active
            exit_code = process.poll()
            if exit_code is None:
                return True
            status = "completed" if exit_code == 0 else "failed"
            self.repository.update_history(history_id, status, exit_code)
            self._active_processes.pop(tool_id, None)
            self.logger.info(
                "プロセス終了 tool_id=%s exit_code=%s", tool_id, exit_code
            )
            return False
        row = self.repository.latest_running_history(tool_id)
        if row is None or row["pid"] is None:
            return False
        try:
            process = psutil.Process(row["pid"])
            same_process = (
                row["process_create_time"] is not None
                and abs(process.create_time() - row["process_create_time"]) < 0.01
                and process.is_running()
                and process.status() != psutil.STATUS_ZOMBIE
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            same_process = False
        if not same_process:
            self.repository.update_history(row["id"], "failed")
        return same_process

    def start(self, tool: Tool) -> subprocess.Popen:
        if tool.id is None:
            raise ValueError("未保存のツールは実行できません。")
        if not tool.allow_multiple_instances and self.is_running(tool.id):
            raise AlreadyRunningError("このツールはすでに実行中です。")
        kwargs: dict = {
            "cwd": resolve_working_directory(tool),
            "shell": False,
        }
        if sys.platform == "win32" and not tool.show_console:
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        process = self.process_factory(build_command(tool), **kwargs)
        create_time = psutil.Process(process.pid).create_time()
        history_id = self.repository.create_history(
            ExecutionHistory(
                tool_id=tool.id,
                pid=process.pid,
                process_create_time=create_time,
                started_at=datetime.now().astimezone().isoformat(timespec="seconds"),
                status="running",
            )
        )
        self._active_processes[tool.id] = (process, history_id)
        self.logger.info("プロセス起動 tool_id=%s pid=%s", tool.id, process.pid)
        return process

    def stop(self, tool_id: int, timeout: float = 3.0) -> None:
        row = self.repository.latest_running_history(tool_id)
        if row is None or not self.is_running(tool_id):
            return
        parent = psutil.Process(row["pid"])
        processes = parent.children(recursive=True) + [parent]
        for process in reversed(processes):
            try:
                process.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.logger.exception("プロセスの通常終了に失敗 pid=%s", process.pid)
        _, alive = psutil.wait_procs(processes, timeout=timeout)
        for process in alive:
            try:
                process.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.logger.exception("プロセスの強制終了に失敗 pid=%s", process.pid)
        self.repository.update_history(row["id"], "stopped")
        self._active_processes.pop(tool_id, None)
        self.logger.info("プロセス停止 tool_id=%s", tool_id)

    def refresh_statuses(self, tools: list[Tool]) -> None:
        for tool in tools:
            if tool.id is not None and tool.status == "running":
                self.is_running(tool.id)
