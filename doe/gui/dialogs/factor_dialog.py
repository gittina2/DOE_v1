"""Dialog for adding and editing experimental factors."""
from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QListWidget,
    QPushButton,
    QWidget,
    QStackedWidget,
    QMessageBox,
    QGroupBox,
)

from doe.models import Factor, DomainValidationError, DoeError


class FactorDialog(QDialog):
    """Adaptive dialog for creating or editing a Factor.

    Displays different fields depending on the selected factor type:
    - Continuous: name, unit, lower_bound, upper_bound
    - Categorical: name, unit, levels list
    """

    def __init__(self, factor: Optional[Factor] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._result_factor: Optional[Factor] = None
        self._editing = factor is not None

        self.setWindowTitle("Edit Factor" if self._editing else "Add Factor")
        self.setMinimumWidth(420)
        self.setModal(True)

        self._init_ui()

        if factor:
            self._populate_from_factor(factor)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Factor type selector
        type_form = QFormLayout()
        self.type_combo = QComboBox(self)
        self.type_combo.addItems(["Continuous", "Categorical"])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_form.addRow("Factor Type:", self.type_combo)
        layout.addLayout(type_form)

        # Common fields
        common_form = QFormLayout()
        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText("e.g., Temperature")
        common_form.addRow("Name:", self.name_edit)

        self.unit_edit = QLineEdit(self)
        self.unit_edit.setPlaceholderText("e.g., \u00b0C (optional)")
        common_form.addRow("Unit:", self.unit_edit)
        layout.addLayout(common_form)

        # Stacked widget for type-specific fields
        self.type_stack = QStackedWidget(self)

        # --- Page 0: Continuous fields ---
        continuous_group = QGroupBox("Continuous Factor Bounds", self)
        continuous_layout = QFormLayout(continuous_group)
        self.lower_bound_edit = QLineEdit(self)
        self.lower_bound_edit.setPlaceholderText("e.g., 20.0")
        continuous_layout.addRow("Lower Bound:", self.lower_bound_edit)
        self.upper_bound_edit = QLineEdit(self)
        self.upper_bound_edit.setPlaceholderText("e.g., 80.0")
        continuous_layout.addRow("Upper Bound:", self.upper_bound_edit)
        self.type_stack.addWidget(continuous_group)

        # --- Page 1: Categorical fields ---
        categorical_group = QGroupBox("Category Levels", self)
        categorical_layout = QVBoxLayout(categorical_group)

        level_input_layout = QHBoxLayout()
        self.level_input = QLineEdit(self)
        self.level_input.setPlaceholderText("Enter a level value")
        self.level_input.returnPressed.connect(self._add_level)
        level_input_layout.addWidget(self.level_input)

        self.add_level_btn = QPushButton("Add Level", self)
        self.add_level_btn.clicked.connect(self._add_level)
        level_input_layout.addWidget(self.add_level_btn)
        categorical_layout.addLayout(level_input_layout)

        self.levels_list = QListWidget(self)
        categorical_layout.addWidget(self.levels_list)

        self.remove_level_btn = QPushButton("Remove Level", self)
        self.remove_level_btn.clicked.connect(self._remove_selected_level)
        categorical_layout.addWidget(self.remove_level_btn)

        self.type_stack.addWidget(categorical_group)
        layout.addWidget(self.type_stack)

        # Dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    # -- Type switching --

    def _on_type_changed(self, index: int) -> None:
        """Switch between Continuous (0) and Categorical (1) field pages."""
        self.type_stack.setCurrentIndex(index)

    # -- Categorical level management --

    def _add_level(self) -> None:
        text = self.level_input.text().strip()
        if text:
            self.levels_list.addItem(text)
            self.level_input.clear()
            self.level_input.setFocus()

    def _remove_selected_level(self) -> None:
        current = self.levels_list.currentRow()
        if current >= 0:
            self.levels_list.takeItem(current)

    # -- Pre-population for editing --

    def _populate_from_factor(self, factor: Factor) -> None:
        """Fill form fields from an existing Factor."""
        self.name_edit.setText(factor.name)
        self.unit_edit.setText(factor.unit or "")

        if factor.type == "continuous":
            self.type_combo.setCurrentIndex(0)
            if factor.lower_bound is not None:
                self.lower_bound_edit.setText(str(factor.lower_bound))
            if factor.upper_bound is not None:
                self.upper_bound_edit.setText(str(factor.upper_bound))
        elif factor.type == "categorical":
            self.type_combo.setCurrentIndex(1)
            if factor.levels:
                for level in factor.levels:
                    self.levels_list.addItem(str(level))

    # -- Factor construction and validation --

    @staticmethod
    def _parse_level_value(text: str) -> Any:
        """Try to parse a level as int, then float, otherwise keep as string."""
        try:
            return int(text)
        except ValueError:
            pass
        try:
            return float(text)
        except ValueError:
            pass
        return text

    def _build_factor(self) -> Factor:
        """Construct a Factor from the current dialog state."""
        name = self.name_edit.text().strip()
        unit = self.unit_edit.text().strip() or None
        factor_type = "continuous" if self.type_combo.currentIndex() == 0 else "categorical"

        if factor_type == "continuous":
            lower_text = self.lower_bound_edit.text().strip()
            upper_text = self.upper_bound_edit.text().strip()

            lower_bound = None
            upper_bound = None

            if lower_text:
                try:
                    lower_bound = float(lower_text)
                except ValueError:
                    raise DomainValidationError(
                        f"Lower Bound must be a number. Got: '{lower_text}'"
                    )

            if upper_text:
                try:
                    upper_bound = float(upper_text)
                except ValueError:
                    raise DomainValidationError(
                        f"Upper Bound must be a number. Got: '{upper_text}'"
                    )

            return Factor(
                name=name,
                type="continuous",
                unit=unit,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
            )
        else:
            levels = []
            for i in range(self.levels_list.count()):
                item_text = self.levels_list.item(i).text()
                levels.append(self._parse_level_value(item_text))

            return Factor(
                name=name,
                type="categorical",
                unit=unit,
                levels=levels if levels else None,
            )

    def _on_accept(self) -> None:
        """Validate and accept the dialog."""
        try:
            factor = self._build_factor()
            factor.validate()
            self._result_factor = factor
            self.accept()
        except (DomainValidationError, DoeError) as e:
            QMessageBox.warning(self, "Validation Error", str(e))

    def get_factor(self) -> Optional[Factor]:
        """Returns the validated Factor, or None if cancelled."""
        return self._result_factor