from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ExecutionHistory:
    tool_id: int
    started_at: str
    status: str
    id: int | None = None
    pid: int | None = None
    process_create_time: float | None = None
    finished_at: str | None = None
    exit_code: int | None = None

