from __future__ import annotations

import os
import logging
from pathlib import Path
from urllib.parse import urlparse

from local_tool_manager.database import ToolRepository
from local_tool_manager.models import Tool


class ValidationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("\n".join(errors))
        self.errors = errors


class ToolService:
    def __init__(self, repository: ToolRepository) -> None:
        self.repository = repository

    def save(self, tool: Tool) -> Tool:
        self.validate(tool)
        is_update = tool.id is not None
        saved = self.repository.update(tool) if is_update else self.repository.create(tool)
        logging.getLogger(__name__).info(
            "ツール%s id=%s", "更新" if is_update else "登録", saved.id
        )
        return saved

    def delete(self, tool_id: int) -> None:
        self.repository.delete(tool_id)
        logging.getLogger(__name__).info("ツール削除 id=%s", tool_id)

    @staticmethod
    def validate(tool: Tool) -> None:
        errors: list[str] = []
        if not tool.name.strip():
            errors.append("名前を入力してください。")
        if tool.entry_type not in {"command", "url"}:
            errors.append("種類を選択してください。")
        elif tool.entry_type == "command":
            if not tool.command.strip():
                errors.append("実行コマンドを入力してください。")
            if tool.working_directory and not Path(tool.working_directory).is_dir():
                errors.append("実行ディレクトリが存在しません。")
            command = os.path.expandvars(tool.command.strip().strip('"'))
            command_path = Path(command)
            if (
                not command_path.is_absolute()
                and tool.working_directory.strip()
                and any(sep in command for sep in "\\/")
            ):
                command_path = Path(
                    os.path.expandvars(tool.working_directory.strip())
                ) / command_path
            if (
                command
                and (command_path.is_absolute() or any(sep in command for sep in "\\/"))
                and not command_path.is_file()
            ):
                errors.append("実行コマンドのファイルが存在しません。")
        elif tool.entry_type == "url":
            parsed = urlparse(tool.url.strip())
            if not tool.url.strip():
                errors.append("URLを入力してください。")
            elif parsed.scheme not in {"http", "https"} or not parsed.netloc:
                errors.append("URLは http:// または https:// で始めてください。")
        if errors:
            raise ValidationError(errors)
