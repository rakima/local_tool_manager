from __future__ import annotations

import logging
import os
import webbrowser

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from local_tool_manager.database import ToolRepository
from local_tool_manager.models import Tool
from local_tool_manager.services import (
    AlreadyRunningError,
    ProcessService,
    ToolService,
    extract_placeholders,
    render_url,
)

from .parameter_dialog import ParameterDialog


STATUS_LABELS = {
    "running": "実行中",
    "failed": "異常終了",
    "completed": "停止中",
    "stopped": "停止中",
}


class ExecutionTab(QWidget):
    edit_requested = Signal(object, bool)

    def __init__(
        self, repository: ToolRepository, process_service: ProcessService, parent=None
    ) -> None:
        super().__init__(parent)
        self.repository = repository
        self.process_service = process_service
        self.tools: list[Tool] = []
        self.search = QLineEdit()
        self.search.setPlaceholderText("名前・説明・カテゴリを検索")
        self.category = QComboBox()
        self.status = QComboBox()
        self.status.addItem("すべての状態", "")
        self.status.addItem("停止中", "stopped")
        self.status.addItem("実行中", "running")
        self.status.addItem("異常終了", "failed")
        self.reload_button = QPushButton("再読み込み")

        filters = QHBoxLayout()
        filters.addWidget(self.search, 2)
        filters.addWidget(self.category)
        filters.addWidget(self.status)
        filters.addWidget(self.reload_button)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["お気に入り", "ツール名", "種類", "カテゴリ", "状態", "最終実行日時", "説明"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet("QTableWidget { outline: none; }")
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        layout = QVBoxLayout(self)
        layout.addLayout(filters)
        layout.addWidget(self.table)

        self.search.textChanged.connect(self.reload)
        self.category.currentIndexChanged.connect(self.reload)
        self.status.currentIndexChanged.connect(self.reload)
        self.reload_button.clicked.connect(self.reload)
        self.table.doubleClicked.connect(lambda: self.run_selected())
        self.table.customContextMenuRequested.connect(self._show_menu)
        self.timer = QTimer(self)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.reload)
        self.timer.start()
        self.reload()

    def reload(self) -> None:
        category = self.category.currentData() or ""
        categories = self.repository.categories()
        current = category
        self.category.blockSignals(True)
        self.category.clear()
        self.category.addItem("すべてのカテゴリ", "")
        for value in categories:
            self.category.addItem(value, value)
        index = self.category.findData(current)
        self.category.setCurrentIndex(max(index, 0))
        self.category.blockSignals(False)
        self.tools = self.repository.list(
            self.search.text(), current, self.status.currentData() or ""
        )
        self.process_service.refresh_statuses(self.tools)
        self.tools = self.repository.list(
            self.search.text(), current, self.status.currentData() or ""
        )
        self.table.setRowCount(len(self.tools))
        for row, tool in enumerate(self.tools):
            values = [
                "★" if tool.is_favorite else "",
                tool.name,
                "コマンド" if tool.entry_type == "command" else "URL",
                tool.category,
                STATUS_LABELS.get(tool.status, "停止中"),
                tool.last_run_at or "",
                tool.description,
            ]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))

    def selected_tool(self) -> Tool | None:
        row = self.table.currentRow()
        return self.tools[row] if 0 <= row < len(self.tools) else None

    def run_selected(self) -> None:
        tool = self.selected_tool()
        if not tool:
            return
        try:
            if tool.entry_type == "url":
                url = tool.url
                names = extract_placeholders(url)
                if names:
                    dialog = ParameterDialog(names, self)
                    if not dialog.exec():
                        return
                    url = render_url(url, dialog.values())
                if not webbrowser.open(url):
                    raise RuntimeError("既定ブラウザでURLを開けませんでした。")
            else:
                self.process_service.start(tool)
            self.reload()
        except AlreadyRunningError as error:
            QMessageBox.information(self, "実行", str(error))
        except Exception as error:
            logging.getLogger(__name__).exception("実行失敗 tool_id=%s", tool.id)
            QMessageBox.critical(self, "実行エラー", f"実行できませんでした。\n{error}")

    def stop_selected(self) -> None:
        tool = self.selected_tool()
        if not tool or tool.id is None:
            return
        try:
            self.process_service.stop(tool.id)
            self.reload()
        except Exception as error:
            logging.getLogger(__name__).exception("停止失敗 tool_id=%s", tool.id)
            QMessageBox.critical(self, "停止エラー", f"停止できませんでした。\n{error}")

    def edit_selected(self, duplicate: bool = False) -> None:
        tool = self.selected_tool()
        if tool:
            self.edit_requested.emit(tool, duplicate)

    def delete_selected(self) -> None:
        tool = self.selected_tool()
        if not tool or tool.id is None:
            return
        if self.process_service.is_running(tool.id):
            QMessageBox.warning(self, "削除", "実行中のツールは削除できません。")
            return
        if QMessageBox.question(
            self, "削除確認", f"「{tool.name}」を削除しますか？"
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            ToolService(self.repository).delete(tool.id)
            self.reload()
        except Exception as error:
            QMessageBox.critical(self, "削除エラー", f"削除できませんでした。\n{error}")

    def open_directory(self) -> None:
        tool = self.selected_tool()
        if not tool:
            return
        path = tool.working_directory
        if not path and tool.command:
            path = os.path.dirname(tool.command.strip('"'))
        try:
            os.startfile(path)
        except Exception as error:
            QMessageBox.critical(
                self, "フォルダを開く", f"実行ディレクトリを開けませんでした。\n{error}"
            )

    def _show_menu(self, position) -> None:
        tool = self.selected_tool()
        if not tool:
            return
        menu = QMenu(self)
        run_action = menu.addAction("実行")
        stop_action = menu.addAction("停止")
        menu.addSeparator()
        edit_action = menu.addAction("編集")
        duplicate_action = menu.addAction("複製")
        delete_action = menu.addAction("削除")
        menu.addSeparator()
        directory_action = menu.addAction("実行ディレクトリを開く")
        is_url = tool.entry_type == "url"
        stop_action.setEnabled(not is_url)
        directory_action.setEnabled(not is_url)
        run_action.triggered.connect(self.run_selected)
        stop_action.triggered.connect(self.stop_selected)
        edit_action.triggered.connect(lambda: self.edit_selected(False))
        duplicate_action.triggered.connect(lambda: self.edit_selected(True))
        delete_action.triggered.connect(self.delete_selected)
        directory_action.triggered.connect(self.open_directory)
        menu.exec(self.table.viewport().mapToGlobal(position))
