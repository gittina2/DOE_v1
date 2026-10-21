"""Functional Experiment view for defining and creating experiments."""
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QMessageBox,
    QScrollArea,
    QFrame,
    QAbstractItemView,
)

from doe.gui.session import GuiSession
from doe.gui.dialogs.factor_dialog import FactorDialog
from doe.gui.dialogs.response_dialog import ResponseDialog
from doe.models import Factor, Response, DomainValidationError, DoeError
from doe.experiment_creation import create_experiment


class ExperimentView(QWidget):
    """Full experiment definition view.

    Allows users to define experiment name, description, factors, and
    responses, then calls the core create_experiment() function to
    produce a validated WorkflowState.
    """

    content_modified = Signal()

    def __init__(self, session: GuiSession, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.session = session

        # Pending factor/response definitions (editable before creation)
        self._factors: List[Factor] = []
        self._responses: List[Response] = []

        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        # Wrap everything in a scroll area
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(24, 20, 24, 20)
        self._content_layout.setSpacing(16)

        # -- Section Header --
        header = QLabel("Experiment Definition", content)
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #1a1a1a;")
        self._content_layout.addWidget(header)

        # -- Name & Description --
        info_group = QGroupBox("Experiment Information", content)
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(8)

        self.name_edit = QLineEdit(info_group)
        self.name_edit.setPlaceholderText("Enter experiment name (required)")
        self.name_edit.textChanged.connect(self._on_field_changed)
        info_layout.addRow("Experiment Name:", self.name_edit)

        self.description_edit = QTextEdit(info_group)
        self.description_edit.setPlaceholderText("Enter an optional description...")
        self.description_edit.setMaximumHeight(80)
        self.description_edit.textChanged.connect(self._on_field_changed)
        info_layout.addRow("Description:", self.description_edit)

        self._content_layout.addWidget(info_group)

        # -- Factors Section --
        factors_group = QGroupBox("Factors", content)
        factors_layout = QVBoxLayout(factors_group)

        # Factor action buttons
        factor_btn_layout = QHBoxLayout()
        factor_btn_layout.addStretch(1)

        self.add_factor_btn = QPushButton("Add Factor", factors_group)
        self.add_factor_btn.clicked.connect(self._on_add_factor)
        factor_btn_layout.addWidget(self.add_factor_btn)

        self.edit_factor_btn = QPushButton("Edit Factor", factors_group)
        self.edit_factor_btn.clicked.connect(self._on_edit_factor)
        self.edit_factor_btn.setEnabled(False)
        factor_btn_layout.addWidget(self.edit_factor_btn)

        self.remove_factor_btn = QPushButton("Remove Factor", factors_group)
        self.remove_factor_btn.clicked.connect(self._on_remove_factor)
        self.remove_factor_btn.setEnabled(False)
        factor_btn_layout.addWidget(self.remove_factor_btn)

        factors_layout.addLayout(factor_btn_layout)

        # Factor table
        self.factor_table = QTableWidget(0, 4, factors_group)
        self.factor_table.setHorizontalHeaderLabels(["Name", "Type", "Details", "Unit"])
        self.factor_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.factor_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.factor_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.factor_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.factor_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.factor_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.factor_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.factor_table.verticalHeader().setVisible(False)
        self.factor_table.setMinimumHeight(120)
        self.factor_table.itemSelectionChanged.connect(self._on_factor_selection_changed)
        self.factor_table.doubleClicked.connect(self._on_edit_factor)
        factors_layout.addWidget(self.factor_table)

        self._content_layout.addWidget(factors_group)

        # -- Responses Section --
        responses_group = QGroupBox("Responses", content)
        responses_layout = QVBoxLayout(responses_group)

        # Response action buttons
        response_btn_layout = QHBoxLayout()
        response_btn_layout.addStretch(1)

        self.add_response_btn = QPushButton("Add Response", responses_group)
        self.add_response_btn.clicked.connect(self._on_add_response)
        response_btn_layout.addWidget(self.add_response_btn)

        self.edit_response_btn = QPushButton("Edit Response", responses_group)
        self.edit_response_btn.clicked.connect(self._on_edit_response)
        self.edit_response_btn.setEnabled(False)
        response_btn_layout.addWidget(self.edit_response_btn)

        self.remove_response_btn = QPushButton("Remove Response", responses_group)
        self.remove_response_btn.clicked.connect(self._on_remove_response)
        self.remove_response_btn.setEnabled(False)
        response_btn_layout.addWidget(self.remove_response_btn)

        responses_layout.addLayout(response_btn_layout)

        # Response table
        self.response_table = QTableWidget(0, 2, responses_group)
        self.response_table.setHorizontalHeaderLabels(["Name", "Unit"])
        self.response_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.response_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.response_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.response_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.response_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.response_table.verticalHeader().setVisible(False)
        self.response_table.setMinimumHeight(100)
        self.response_table.itemSelectionChanged.connect(self._on_response_selection_changed)
        self.response_table.doubleClicked.connect(self._on_edit_response)
        responses_layout.addWidget(self.response_table)

        self._content_layout.addWidget(responses_group)

        # -- Create Experiment Button --
        create_btn_layout = QHBoxLayout()
        create_btn_layout.addStretch(1)
        self.create_btn = QPushButton("Create Experiment", content)
        self.create_btn.setMinimumHeight(38)
        self.create_btn.setMinimumWidth(200)
        self.create_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2563eb;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
            """
        )
        self.create_btn.clicked.connect(self._on_create_experiment)
        create_btn_layout.addWidget(self.create_btn)
        create_btn_layout.addStretch(1)
        self._content_layout.addLayout(create_btn_layout)

        # -- Experiment Summary (hidden until creation) --
        self.summary_group = QGroupBox("Experiment Summary", content)
        self.summary_group.setVisible(False)
        summary_layout = QVBoxLayout(self.summary_group)
        self.summary_label = QLabel(self.summary_group)
        self.summary_label.setWordWrap(True)
        self.summary_label.setTextFormat(Qt.RichText)
        self.summary_label.setStyleSheet("font-size: 13px; line-height: 1.5; color: #333333;")
        summary_layout.addWidget(self.summary_label)
        self._content_layout.addWidget(self.summary_group)

        self._content_layout.addStretch(1)

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

    def _connect_signals(self) -> None:
        self.session.state_changed.connect(self._on_session_state_changed)

    def _on_field_changed(self) -> None:
        self.content_modified.emit()

    # ------------------------------------------------------------------ #
    #  Session synchronization                                            #
    # ------------------------------------------------------------------ #

    def _on_session_state_changed(self, state) -> None:
        """React to workflow state changes (e.g. file loaded, new workflow)."""
        experiment = state.experiment if state else None
        if experiment is not None:
            self._populate_from_experiment(experiment)
            self._show_summary(experiment)
        else:
            self._clear_form()
            self._hide_summary()

    def _populate_from_experiment(self, experiment) -> None:
        """Fill form and factor/response tables from an Experiment object."""
        self.name_edit.blockSignals(True)
        self.description_edit.blockSignals(True)

        self.name_edit.setText(experiment.name)
        self.description_edit.setPlainText(experiment.description or "")

        self.name_edit.blockSignals(False)
        self.description_edit.blockSignals(False)

        self._factors = list(experiment.factors)
        self._responses = list(experiment.responses)
        self._refresh_factor_table()
        self._refresh_response_table()

    def _clear_form(self) -> None:
        """Reset all form fields to empty."""
        self.name_edit.blockSignals(True)
        self.description_edit.blockSignals(True)

        self.name_edit.clear()
        self.description_edit.clear()

        self.name_edit.blockSignals(False)
        self.description_edit.blockSignals(False)

        self._factors.clear()
        self._responses.clear()
        self._refresh_factor_table()
        self._refresh_response_table()

    # ------------------------------------------------------------------ #
    #  Uncommitted Changes Tracking                                       #
    # ------------------------------------------------------------------ #

    def has_uncommitted_changes(self) -> bool:
        """Check if current form inputs differ from the session's experiment."""
        exp = self.session.workflow_state.experiment
        current_name = self.name_edit.text().strip()
        current_desc = self.description_edit.toPlainText().strip()

        if exp is None:
            return bool(current_name or current_desc or self._factors or self._responses)

        exp_desc = (exp.description or "").strip()
        if current_name != exp.name or current_desc != exp_desc:
            return True

        if self._factors != list(exp.factors):
            return True

        if self._responses != list(exp.responses):
            return True

        return False

    # ------------------------------------------------------------------ #
    #  Factor CRUD                                                        #
    # ------------------------------------------------------------------ #

    def _on_add_factor(self) -> None:
        dialog = FactorDialog(parent=self)
        if dialog.exec() == FactorDialog.Accepted:
            factor = dialog.get_factor()
            if factor:
                self._factors.append(factor)
                self._refresh_factor_table()
                self.content_modified.emit()

    def _on_edit_factor(self) -> None:
        row = self.factor_table.currentRow()
        if row < 0 or row >= len(self._factors):
            return
        dialog = FactorDialog(factor=self._factors[row], parent=self)
        if dialog.exec() == FactorDialog.Accepted:
            factor = dialog.get_factor()
            if factor:
                self._factors[row] = factor
                self._refresh_factor_table()
                self.content_modified.emit()

    def _on_remove_factor(self) -> None:
        row = self.factor_table.currentRow()
        if row < 0 or row >= len(self._factors):
            return
        factor_name = self._factors[row].name
        reply = QMessageBox.question(
            self,
            "Remove Factor",
            f"Are you sure you want to remove factor '{factor_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            del self._factors[row]
            self._refresh_factor_table()
            self.content_modified.emit()

    def _on_factor_selection_changed(self) -> None:
        has_selection = bool(self.factor_table.selectedItems())
        self.edit_factor_btn.setEnabled(has_selection)
        self.remove_factor_btn.setEnabled(has_selection)

    def _refresh_factor_table(self) -> None:
        self.factor_table.setRowCount(len(self._factors))
        for row, factor in enumerate(self._factors):
            self.factor_table.setItem(row, 0, QTableWidgetItem(factor.name))

            type_display = factor.type.capitalize()
            self.factor_table.setItem(row, 1, QTableWidgetItem(type_display))

            if factor.type == "continuous":
                lb = factor.lower_bound if factor.lower_bound is not None else "?"
                ub = factor.upper_bound if factor.upper_bound is not None else "?"
                details = f"[{lb}, {ub}]"
            elif factor.type == "categorical" and factor.levels:
                details = ", ".join(str(lv) for lv in factor.levels)
            else:
                details = ""
            self.factor_table.setItem(row, 2, QTableWidgetItem(details))

            self.factor_table.setItem(row, 3, QTableWidgetItem(factor.unit or ""))

        self.edit_factor_btn.setEnabled(False)
        self.remove_factor_btn.setEnabled(False)

    # ------------------------------------------------------------------ #
    #  Response CRUD                                                      #
    # ------------------------------------------------------------------ #

    def _on_add_response(self) -> None:
        dialog = ResponseDialog(parent=self)
        if dialog.exec() == ResponseDialog.Accepted:
            response = dialog.get_response()
            if response:
                self._responses.append(response)
                self._refresh_response_table()
                self.content_modified.emit()

    def _on_edit_response(self) -> None:
        row = self.response_table.currentRow()
        if row < 0 or row >= len(self._responses):
            return
        dialog = ResponseDialog(response=self._responses[row], parent=self)
        if dialog.exec() == ResponseDialog.Accepted:
            response = dialog.get_response()
            if response:
                self._responses[row] = response
                self._refresh_response_table()
                self.content_modified.emit()

    def _on_remove_response(self) -> None:
        row = self.response_table.currentRow()
        if row < 0 or row >= len(self._responses):
            return
        response_name = self._responses[row].name
        reply = QMessageBox.question(
            self,
            "Remove Response",
            f"Are you sure you want to remove response '{response_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            del self._responses[row]
            self._refresh_response_table()
            self.content_modified.emit()

    def _on_response_selection_changed(self) -> None:
        has_selection = bool(self.response_table.selectedItems())
        self.edit_response_btn.setEnabled(has_selection)
        self.remove_response_btn.setEnabled(has_selection)

    def _refresh_response_table(self) -> None:
        self.response_table.setRowCount(len(self._responses))
        for row, response in enumerate(self._responses):
            self.response_table.setItem(row, 0, QTableWidgetItem(response.name))
            self.response_table.setItem(row, 1, QTableWidgetItem(response.unit or ""))

        self.edit_response_btn.setEnabled(False)
        self.remove_response_btn.setEnabled(False)

    # ------------------------------------------------------------------ #
    #  Experiment creation                                                #
    # ------------------------------------------------------------------ #

    def _on_create_experiment(self) -> bool:
        """Collect form data, check for downstream reset, call create_experiment().

        Returns True on successful experiment creation, False otherwise.
        """
        # Check for downstream data that would be invalidated
        state = self.session.workflow_state
        has_downstream = (
            state.design is not None
            or state.results is not None
            or state.analysis is not None
        )

        if has_downstream:
            reply = QMessageBox.warning(
                self,
                "Replace Existing Experiment",
                "Creating a new experiment will reset the current workflow.\n\n"
                "The existing design, results, and analysis data will no longer "
                "be part of the active workflow.\n\n"
                "Do you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return False

        # Collect form data
        name = self.name_edit.text().strip()
        description = self.description_edit.toPlainText().strip() or None

        try:
            new_state = create_experiment(
                name=name,
                factors=list(self._factors),
                responses=list(self._responses),
                description=description,
            )
            self.session.set_workflow_state(new_state, is_dirty=True)
            self._show_summary(new_state.experiment)
            return True
        except (DomainValidationError, DoeError) as e:
            QMessageBox.warning(
                self,
                "Experiment Validation Error",
                f"Could not create the experiment:\n\n{str(e)}",
            )
            return False

    apply_experiment = _on_create_experiment

    # ------------------------------------------------------------------ #
    #  Summary display                                                    #
    # ------------------------------------------------------------------ #

    def _show_summary(self, experiment) -> None:
        """Display a concise summary of the created experiment."""
        lines = []
        lines.append(f"<b>Experiment:</b> {experiment.name}")
        if experiment.description:
            lines.append(f"<b>Description:</b> {experiment.description}")

        lines.append("")
        lines.append(f"<b>Factors ({len(experiment.factors)}):</b>")
        for f in experiment.factors:
            if f.type == "continuous":
                detail = f"[{f.lower_bound}, {f.upper_bound}]"
            elif f.type == "categorical" and f.levels:
                detail = ", ".join(str(lv) for lv in f.levels)
            else:
                detail = ""
            unit_str = f" ({f.unit})" if f.unit else ""
            lines.append(f"&nbsp;&nbsp;\u2022 {f.name}{unit_str} \u2014 {f.type.capitalize()} {detail}")

        lines.append("")
        lines.append(f"<b>Responses ({len(experiment.responses)}):</b>")
        for r in experiment.responses:
            unit_str = f" ({r.unit})" if r.unit else ""
            lines.append(f"&nbsp;&nbsp;\u2022 {r.name}{unit_str}")

        self.summary_label.setText("<br>".join(lines))
        self.summary_group.setVisible(True)

    def _hide_summary(self) -> None:
        self.summary_group.setVisible(False)
        self.summary_label.clear()