from unittest.mock import Mock, patch

from PySide6.QtWidgets import QApplication, QMessageBox

from local_tool_manager.ui.settings_tab import SettingsTab


def create_tab() -> SettingsTab:
    QApplication.instance() or QApplication([])
    return SettingsTab(Mock(), Mock())


def test_entry_type_switches_visible_rows():
    tab = create_tab()

    assert tab.form.isRowVisible(tab._command_rows[1])
    assert not tab.form.isRowVisible(tab.url)

    tab.entry_type.setCurrentIndex(1)

    assert not tab.form.isRowVisible(tab._command_rows[1])
    assert tab.form.isRowVisible(tab.url)


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
