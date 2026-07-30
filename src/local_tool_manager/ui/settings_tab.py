from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from local_tool_manager.models import Tool
from local_tool_manager.services import ProcessService
from local_tool_manager.services.tool_service import ToolService, ValidationError


class SettingsTab(QWidget):
    saved = Signal()
    deleted = Signal()

    def __init__(
        self, service: ToolService, process_service: ProcessService, parent=None
    ) -> None:
        super().__init__(parent)
        self.service = service
        self.process_service = process_service
        self.current_id: int | None = None
        self._original: Tool | None = None
        self._baseline: tuple | None = None

        self.name = QLineEdit()
        self.description = QTextEdit()
        self.description.setMaximumHeight(80)
        self.category = QLineEdit()
        self.entry_type = QComboBox()
        self.entry_type.addItem("コマンド", "command")
        self.entry_type.addItem("URL", "url")
        self.favorite = QCheckBox("お気に入り")
        self.working_directory = QLineEdit()
        self.command = QLineEdit()
        self.arguments = QLineEdit()
        self.url = QLineEdit()
        self.allow_multiple = QCheckBox("多重起動を許可")
        self.show_console = QCheckBox("コンソールを表示する")

        directory_row = self._browse_row(
            self.working_directory, "参照...", self._select_directory
        )
        command_row = self._browse_row(self.command, "参照...", self._select_command)
        self.form = QFormLayout()
        self.form.addRow("名前 *", self.name)
        self.form.addRow("説明", self.description)
        self.form.addRow("カテゴリ", self.category)
        self.form.addRow("種類 *", self.entry_type)
        self.form.addRow("", self.favorite)
        self.form.addRow("実行ディレクトリ", directory_row)
        self.form.addRow("実行コマンド *", command_row)
        self.form.addRow("引数", self.arguments)
        self.form.addRow("URL *", self.url)
        self.form.addRow("", self.allow_multiple)
        self.form.addRow("", self.show_console)
        self._command_rows = (
            directory_row,
            command_row,
            self.arguments,
            self.allow_multiple,
            self.show_console,
        )

        self.new_button = QPushButton("新規")
        self.save_button = QPushButton("保存")
        self.delete_button = QPushButton("削除")
        self.clear_button = QPushButton("入力クリア")
        buttons = QHBoxLayout()
        for button in (
            self.new_button,
            self.save_button,
            self.delete_button,
            self.clear_button,
        ):
            buttons.addWidget(button)
        buttons.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(self.form)
        layout.addLayout(buttons)
        layout.addStretch()

        self.entry_type.currentIndexChanged.connect(self._update_type_fields)
        self.new_button.clicked.connect(self.new_form)
        self.save_button.clicked.connect(self.save)
        self.delete_button.clicked.connect(self.delete)
        self.clear_button.clicked.connect(self.reset_values)
        self.new_form(confirm=False)

    @staticmethod
    def _browse_row(field: QLineEdit, text: str, callback) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        button = QPushButton(text)
        button.clicked.connect(callback)
        layout.addWidget(field)
        layout.addWidget(button)
        widget.browse_button = button
        return widget

    def _select_directory(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "実行ディレクトリを選択", self.working_directory.text()
        )
        if path:
            self.working_directory.setText(path)

    def _select_command(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "実行コマンドを選択",
            self.working_directory.text(),
            "実行対象 (*.exe *.py *.bat *.cmd);;すべてのファイル (*)",
        )
        if path:
            self.command.setText(path)

    def _update_type_fields(self) -> None:
        is_command = self.entry_type.currentData() == "command"
        for row in self._command_rows:
            self.form.setRowVisible(row, is_command)
        self.form.setRowVisible(self.url, not is_command)

    def new_form(self, *, confirm: bool = True) -> bool:
        if confirm and not self._confirm_discard_changes("新規入力へ切り替えますか？"):
            return False
        self.current_id = None
        self._original = None
        self._clear_fields()
        self._baseline = self._snapshot()
        self.delete_button.setEnabled(False)
        self.name.setFocus()
        return True

    def _clear_fields(self) -> None:
        self.name.clear()
        self.description.clear()
        self.category.clear()
        self.entry_type.setCurrentIndex(0)
        self.favorite.setChecked(False)
        self.working_directory.clear()
        self.command.clear()
        self.arguments.clear()
        self.url.clear()
        self.allow_multiple.setChecked(False)
        self.show_console.setChecked(False)
        self._update_type_fields()

    def reset_values(self) -> None:
        if not self._confirm_discard_changes("入力内容を元に戻しますか？"):
            return
        if self._original:
            self.load_tool(self._original)
        else:
            self._clear_fields()
            self._baseline = self._snapshot()

    def _snapshot(self) -> tuple:
        tool = self._form_tool()
        return (
            tool.id,
            tool.name,
            tool.description,
            tool.category,
            tool.entry_type,
            tool.is_favorite,
            tool.working_directory,
            tool.command,
            tool.arguments,
            tool.url,
            tool.allow_multiple_instances,
            tool.show_console,
        )

    def _confirm_discard_changes(self, message: str) -> bool:
        if self._baseline == self._snapshot():
            return True
        return (
            QMessageBox.question(
                self,
                "未保存の変更",
                f"未保存の変更があります。\n{message}",
            )
            == QMessageBox.StandardButton.Yes
        )

    def load_tool(self, tool: Tool, duplicate: bool = False) -> None:
        self._original = None if duplicate else tool
        self.current_id = None if duplicate else tool.id
        self.name.setText(tool.name + ("のコピー" if duplicate else ""))
        self.description.setPlainText(tool.description)
        self.category.setText(tool.category)
        self.entry_type.setCurrentIndex(0 if tool.entry_type == "command" else 1)
        self.favorite.setChecked(tool.is_favorite)
        self.working_directory.setText(tool.working_directory)
        self.command.setText(tool.command)
        self.arguments.setText(tool.arguments)
        self.url.setText(tool.url)
        self.allow_multiple.setChecked(tool.allow_multiple_instances)
        self.show_console.setChecked(tool.show_console)
        self.delete_button.setEnabled(not duplicate and tool.id is not None)
        self._update_type_fields()
        self._baseline = self._snapshot()

    def _form_tool(self) -> Tool:
        return Tool(
            id=self.current_id,
            name=self.name.text(),
            description=self.description.toPlainText(),
            category=self.category.text(),
            entry_type=self.entry_type.currentData(),
            is_favorite=self.favorite.isChecked(),
            working_directory=self.working_directory.text(),
            command=self.command.text(),
            arguments=self.arguments.text(),
            url=self.url.text(),
            allow_multiple_instances=self.allow_multiple.isChecked(),
            show_console=self.show_console.isChecked(),
        )

    def save(self) -> None:
        try:
            saved = self.service.save(self._form_tool())
        except ValidationError as error:
            QMessageBox.warning(self, "入力エラー", "\n".join(error.errors))
            return
        except Exception as error:
            QMessageBox.critical(self, "保存エラー", f"保存できませんでした。\n{error}")
            return
        self.load_tool(saved)
        self.saved.emit()
        QMessageBox.information(self, "保存", "ツールを保存しました。")

    def delete(self) -> None:
        if self.current_id is None:
            return
        if self.process_service.is_running(self.current_id):
            QMessageBox.warning(self, "削除", "実行中のツールは削除できません。")
            return
        if QMessageBox.question(
            self, "削除確認", "このツールを削除しますか？"
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            self.service.delete(self.current_id)
        except Exception as error:
            QMessageBox.critical(self, "削除エラー", f"削除できませんでした。\n{error}")
            return
        self.new_form(confirm=False)
        self.deleted.emit()
