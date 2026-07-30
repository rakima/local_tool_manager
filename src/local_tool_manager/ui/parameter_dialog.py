from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)


class ParameterDialog(QDialog):
    def __init__(self, names: list[str], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("URLパラメータ")
        self.inputs = {name: QLineEdit(self) for name in names}
        form = QFormLayout()
        for name, field in self.inputs.items():
            form.addRow(f"{name}:", field)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self) -> dict[str, str]:
        return {name: field.text() for name, field in self.inputs.items()}

