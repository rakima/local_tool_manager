from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Tool:
    name: str
    entry_type: str
    id: int | None = None
    description: str = ""
    category: str = ""
    working_directory: str = ""
    command: str = ""
    arguments: str = ""
    url: str = ""
    allow_multiple_instances: bool = False
    show_console: bool = False
    is_favorite: bool = False
    created_at: str = ""
    updated_at: str = ""
    last_run_at: str | None = None
    status: str = "stopped"

