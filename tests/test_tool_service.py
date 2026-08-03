import pytest

from local_tool_manager.models import Tool
from local_tool_manager.services.tool_service import ToolService, ValidationError


def test_accepts_command_relative_to_working_directory(tmp_path):
    script = tmp_path / "scripts" / "main.py"
    script.parent.mkdir()
    script.touch()
    tool = Tool(
        name="相対パス",
        entry_type="command",
        working_directory=str(tmp_path),
        command=r"scripts\main.py",
    )

    ToolService.validate(tool)


def test_rejects_missing_command_relative_to_working_directory(tmp_path):
    tool = Tool(
        name="相対パス",
        entry_type="command",
        working_directory=str(tmp_path),
        command=r"scripts\missing.py",
    )

    with pytest.raises(ValidationError) as error:
        ToolService.validate(tool)

    assert "実行コマンドのファイルが存在しません。" in error.value.errors
