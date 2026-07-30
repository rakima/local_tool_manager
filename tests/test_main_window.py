from unittest.mock import patch

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QMessageBox

from local_tool_manager.models import Tool
from local_tool_manager.ui.main_window import MainWindow


def create_window(repository) -> MainWindow:
    QApplication.instance() or QApplication([])
    return MainWindow(repository)


def test_declining_tab_change_keeps_settings_tab(repository):
    window = create_window(repository)
    window.tabs.setCurrentWidget(window.settings_tab)
    window.settings_tab.name.setText("未保存ツール")

    with patch.object(
        QMessageBox, "question", return_value=QMessageBox.StandardButton.No
    ):
        window.tabs.setCurrentWidget(window.execution_tab)

    assert window.tabs.currentWidget() is window.settings_tab
    assert window.settings_tab.name.text() == "未保存ツール"


def test_declining_edit_request_keeps_unsaved_input(repository):
    window = create_window(repository)
    window.settings_tab.name.setText("未保存ツール")
    other = Tool(id=1, name="別ツール", entry_type="command", command="cmd")

    with patch.object(
        QMessageBox, "question", return_value=QMessageBox.StandardButton.No
    ):
        window._edit_tool(other, duplicate=False)

    assert window.settings_tab.name.text() == "未保存ツール"


def test_declining_close_keeps_window_open(repository):
    window = create_window(repository)
    window.settings_tab.name.setText("未保存ツール")
    event = QCloseEvent()

    with patch.object(
        QMessageBox, "question", return_value=QMessageBox.StandardButton.No
    ):
        window.closeEvent(event)

    assert not event.isAccepted()
