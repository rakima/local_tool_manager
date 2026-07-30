from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QTabWidget

from local_tool_manager.database import ToolRepository
from local_tool_manager.services import ProcessService, ToolService

from .execution_tab import ExecutionTab
from .settings_tab import SettingsTab


class MainWindow(QMainWindow):
    def __init__(self, repository: ToolRepository) -> None:
        super().__init__()
        self.setWindowTitle("Local Tool Manager")
        self.resize(1100, 650)
        tool_service = ToolService(repository)
        process_service = ProcessService(repository)
        self.tabs = QTabWidget()
        self.execution_tab = ExecutionTab(repository, process_service)
        self.settings_tab = SettingsTab(tool_service, process_service)
        self.tabs.addTab(self.execution_tab, "実行")
        self.tabs.addTab(self.settings_tab, "設定")
        self.setCentralWidget(self.tabs)
        self.tabs.setCurrentIndex(0)
        self.execution_tab.edit_requested.connect(self._edit_tool)
        self.settings_tab.saved.connect(self.execution_tab.reload)
        self.settings_tab.deleted.connect(self.execution_tab.reload)

    def _edit_tool(self, tool, duplicate: bool) -> None:
        self.settings_tab.load_tool(tool, duplicate)
        self.tabs.setCurrentWidget(self.settings_tab)
