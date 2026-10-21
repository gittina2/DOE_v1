"""Dialog for adding and editing experimental responses."""
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QWidget,
)

from doe.models import Response, DomainValidationError, DoeError


class ResponseDialog(QDialog):
    """Dialog for creating or editing a Response.

    Only continuous responses are supported by the current core.
    """

    def __init__(self, response: Optional[Response] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._result_response: Optional[Response] = None
        self._editing = response is not None

        self.setWindowTitle("Edit Response" if self._editing else "Add Response")
        self.setMinimumWidth(360)
        self.setModal(True)

        self._init_ui()

        if response:
            self._populate_from_response(response)

    def _init_ui(self) -> None:
        layout = QFormLayout(self)
        layout.setSpacing(10)

        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText("e.g., Yield")
        layout.addRow("Name:", self.name_edit)

        self.unit_edit = QLineEdit(self)
        self.unit_edit.setPlaceholderText("e.g., % (optional)")
        layout.addRow("Unit:", self.unit_edit)

        # Type info label (read-only, always continuous)
        type_label = QLabel("Type: Continuous", self)
        type_label.setStyleSheet("color: #666666; font-style: italic;")
        layout.addRow("", type_label)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

    def _populate_from_response(self, response: Response) -> None:
        """Fill form fields from an existing Response."""
        self.name_edit.setText(response.name)
        self.unit_edit.setText(response.unit or "")

    def _on_accept(self) -> None:
        """Validate and accept the dialog."""
        try:
            name = self.name_edit.text().strip()
            unit = self.unit_edit.text().strip() or None

            response = Response(name=name, type="continuous", unit=unit)
            response.validate()

            self._result_response = response
            self.accept()
        except (DomainValidationError, DoeError) as e:
            QMessageBox.warning(self, "Validation Error", str(e))

    def get_response(self) -> Optional[Response]:
        """Returns the validated Response, or None if cancelled."""
        return self._result_response