from unittest.mock import Mock, patch

from PySide6.QtWidgets import QApplication, QInputDialog, QMessageBox

from local_tool_manager.models import Tool
from local_tool_manager.services.tool_service import ToolService
from local_tool_manager.ui.settings_tab import SettingsTab


def create_tab() -> SettingsTab:
    QApplication.instance() or QApplication([])
    return SettingsTab(Mock(), Mock())


def test_entry_type_switches_visible_rows():
    tab = create_tab()

    assert tab.form.isRowVisible(tab._command_rows[1])
    assert not tab.form.isRowVisible(tab.url)
    assert tab.check_button.isEnabled()

    tab.entry_type.setCurrentIndex(1)

    assert not tab.form.isRowVisible(tab._command_rows[1])
    assert tab.form.isRowVisible(tab.url)
    assert not tab.check_button.isEnabled()


def test_new_form_keeps_unsaved_input_when_discard_is_declined():
    tab = create_tab()
    tab.name.setText("未保存ツール")

    with patch.object(
        QMessageBox, "question", return_value=QMessageBox.StandardButton.No
    ) as question:
        tab.new_button.click()

    assert tab.name.text() == "未保存ツール"
    question.assert_called_once()


def test_clear_resets_unsaved_input_after_confirmation():
    tab = create_tab()
    tab.name.setText("未保存ツール")

    with patch.object(
        QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes
    ) as question:
        tab.reset_values()

    assert tab.name.text() == ""
    question.assert_called_once()


def test_reports_unsaved_changes():
    tab = create_tab()

    assert not tab.has_unsaved_changes()

    tab.name.setText("未保存ツール")

    assert tab.has_unsaved_changes()


def test_copies_registered_tool_as_unsaved_new_tool(repository):
    source = repository.create(
        Tool(
            name="コピー元",
            description="説明",
            category="開発",
            entry_type="command",
            working_directory=r"C:\tools",
            command=r"scripts\main.py",
            arguments="--mode fast",
            allow_multiple_instances=True,
        )
    )
    tab = SettingsTab(ToolService(repository), Mock())

    with patch.object(
        QInputDialog,
        "getItem",
        return_value=(f"{source.name} (ID: {source.id})", True),
    ):
        tab.copy_button.click()

    assert tab.current_id is None
    assert tab.name.text() == "コピー元のコピー"
    assert tab.command.text() == r"scripts\main.py"
    assert tab.arguments.text() == "--mode fast"
    assert tab.allow_multiple.isChecked()
    assert not tab.delete_button.isEnabled()
    assert tab.has_unsaved_changes()


def test_copy_keeps_current_input_when_discard_is_declined(repository):
    repository.create(Tool(name="コピー元", entry_type="command", command="cmd"))
    tab = SettingsTab(ToolService(repository), Mock())
    tab.name.setText("編集中")

    with patch.object(
        QMessageBox, "question", return_value=QMessageBox.StandardButton.No
    ):
        tab.copy_button.click()

    assert tab.name.text() == "編集中"
