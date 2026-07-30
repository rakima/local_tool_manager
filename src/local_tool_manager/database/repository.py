from __future__ import annotations

from dataclasses import fields
from datetime import datetime

from local_tool_manager.models import ExecutionHistory, Tool

from .connection import Database


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class ToolRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(self, tool: Tool) -> Tool:
        now = _now()
        values = self._values(tool)
        with self.database.connect() as connection:
            cursor = connection.execute(
                """INSERT INTO tools (
                    name, description, category, entry_type, working_directory,
                    command, arguments, url, allow_multiple_instances,
                    show_console, is_favorite, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (*values, now, now),
            )
        return self.get(cursor.lastrowid)

    def update(self, tool: Tool) -> Tool:
        if tool.id is None:
            raise ValueError("更新対象のIDがありません。")
        with self.database.connect() as connection:
            connection.execute(
                """UPDATE tools SET
                    name=?, description=?, category=?, entry_type=?,
                    working_directory=?, command=?, arguments=?, url=?,
                    allow_multiple_instances=?, show_console=?, is_favorite=?,
                    updated_at=?
                WHERE id=?""",
                (*self._values(tool), _now(), tool.id),
            )
        return self.get(tool.id)

    def delete(self, tool_id: int) -> None:
        with self.database.connect() as connection:
            connection.execute("DELETE FROM tools WHERE id = ?", (tool_id,))

    def get(self, tool_id: int) -> Tool:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM tools WHERE id = ?", (tool_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"ツールが見つかりません: {tool_id}")
        return self._to_tool(row)

    def list(
        self, search: str = "", category: str = "", status: str = ""
    ) -> list[Tool]:
        query = """
            SELECT t.*,
                (SELECT started_at FROM execution_history
                 WHERE tool_id=t.id ORDER BY started_at DESC LIMIT 1) AS last_run_at,
                (SELECT status FROM execution_history
                 WHERE tool_id=t.id ORDER BY started_at DESC LIMIT 1) AS status
            FROM tools t
            WHERE (? = '' OR lower(t.name || ' ' || coalesce(t.description, '') ||
                   ' ' || coalesce(t.category, '')) LIKE '%' || lower(?) || '%')
              AND (? = '' OR t.category = ?)
              AND (? = '' OR
                   (? = 'stopped' AND coalesce((SELECT status FROM execution_history
                    WHERE tool_id=t.id ORDER BY started_at DESC LIMIT 1), 'stopped')
                    IN ('stopped', 'completed'))
                   OR (? <> 'stopped' AND coalesce((SELECT status FROM execution_history
                    WHERE tool_id=t.id ORDER BY started_at DESC LIMIT 1), 'stopped') = ?))
            ORDER BY t.is_favorite DESC, lower(t.name)
        """
        with self.database.connect() as connection:
            rows = connection.execute(
                query,
                (
                    search,
                    search,
                    category,
                    category,
                    status,
                    status,
                    status,
                    status,
                ),
            ).fetchall()
        return [self._to_tool(row) for row in rows]

    def categories(self) -> list[str]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT DISTINCT category FROM tools "
                "WHERE category IS NOT NULL AND category <> '' ORDER BY category"
            ).fetchall()
        return [row["category"] for row in rows]

    def create_history(self, history: ExecutionHistory) -> int:
        with self.database.connect() as connection:
            cursor = connection.execute(
                """INSERT INTO execution_history (
                    tool_id, pid, process_create_time, started_at, finished_at,
                    exit_code, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    history.tool_id,
                    history.pid,
                    history.process_create_time,
                    history.started_at,
                    history.finished_at,
                    history.exit_code,
                    history.status,
                ),
            )
        return int(cursor.lastrowid)

    def update_history(
        self, history_id: int, status: str, exit_code: int | None = None
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """UPDATE execution_history
                   SET status=?, exit_code=?, finished_at=?
                   WHERE id=?""",
                (status, exit_code, _now(), history_id),
            )

    def latest_running_history(self, tool_id: int):
        with self.database.connect() as connection:
            return connection.execute(
                """SELECT * FROM execution_history
                   WHERE tool_id=? AND status='running'
                   ORDER BY started_at DESC LIMIT 1""",
                (tool_id,),
            ).fetchone()

    @staticmethod
    def _values(tool: Tool) -> tuple:
        return (
            tool.name.strip(),
            tool.description.strip(),
            tool.category.strip(),
            tool.entry_type,
            tool.working_directory.strip(),
            tool.command.strip(),
            tool.arguments,
            tool.url.strip(),
            int(tool.allow_multiple_instances),
            int(tool.show_console),
            int(tool.is_favorite),
        )

    @staticmethod
    def _to_tool(row) -> Tool:
        data = dict(row)
        valid = {field.name for field in fields(Tool)}
        data = {key: value for key, value in data.items() if key in valid}
        for name in ("allow_multiple_instances", "show_console", "is_favorite"):
            data[name] = bool(data.get(name))
        data["status"] = data.get("status") or "stopped"
        return Tool(**data)
