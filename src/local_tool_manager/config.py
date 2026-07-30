from __future__ import annotations

import os
from pathlib import Path


APP_NAME = "local_tool_manager"


def get_data_directory() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME


def ensure_data_directory() -> Path:
    path = get_data_directory()
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_database_path() -> Path:
    return ensure_data_directory() / "local_tool_manager.db"


def get_log_path() -> Path:
    return ensure_data_directory() / "local_tool_manager.log"

