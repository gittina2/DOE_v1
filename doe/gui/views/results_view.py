"""Functional Results view for manual measurement entry, CSV importing, completeness tracking, and template exporting."""
import os
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QMessageBox,
    QScrollArea,
    QFrame,
    QFileDialog,
)

from doe.gui.session import GuiSession
from doe.imports.csv_result_importer import import_results_from_csv
from doe.result_input import insert_results, export_results_template_csv
from doe.models import ResultEntry, DoeError, DomainValidationError


class ResultsView(QWidget):
    """Interactive experimental response entry, CSV ingestion, and tracking view."""

    results_updated = Signal()

    def __init__(self, session: GuiSession, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.session = session
        self._is_populating = False

        self._init_ui()
        self._connect_signals()
        self._refresh_view()

    def _init_ui(self) -> None:
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
        header = QLabel("Experimental Results & Measurements", content)
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #1a1a1a;")
        self._content_layout.addWidget(header)

        # -- Status & Completeness Header Banner --
        self.status_frame = QFrame(content)
        self.status_frame.setStyleSheet(
            """
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 10px;
            }
            """
        )
        status_layout = QHBoxLayout(self.status_frame)
        status_layout.setContentsMargins(8, 8, 8, 8)

        self.status_badge = QLabel("No Results", self.status_frame)
        self.status_badge.setStyleSheet(
            """
            QLabel {
                background-color: #64748b;
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 4px;
                padding: 4px 10px;
            }
            """
        )
        status_layout.addWidget(self.status_badge)

        self.status_text_label = QLabel(self.status_frame)
        self.status_text_label.setStyleSheet("font-size: 13px; color: #334155;")
        status_layout.addWidget(self.status_text_label, 1)

        self._content_layout.addWidget(self.status_frame)

        # -- Action Toolbar --
        toolbar_group = QGroupBox("Results Management", content)
        toolbar_layout = QHBoxLayout(toolbar_group)

        self.export_template_btn = QPushButton("Export Results Template (CSV)...", toolbar_group)
        self.export_template_btn.clicked.connect(self._on_export_template)
        toolbar_layout.addWidget(self.export_template_btn)

        self.import_csv_btn = QPushButton("Import Results from CSV...", toolbar_group)
        self.import_csv_btn.setStyleSheet("font-weight: bold;")
        self.import_csv_btn.clicked.connect(self._on_import_csv)
        toolbar_layout.addWidget(self.import_csv_btn)

        self.save_btn = QPushButton("Save / Apply Results", toolbar_group)
        self.save_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #16a34a;
                color: white;
                font-weight: bold;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #15803d;
            }
            """
        )
        self.save_btn.clicked.connect(self._on_save_results)
        toolbar_layout.addWidget(self.save_btn)

        self.clear_btn = QPushButton("Clear Results", toolbar_group)
        self.clear_btn.clicked.connect(self._on_clear_results)
        toolbar_layout.addWidget(self.clear_btn)

        toolbar_layout.addStretch(1)
        self._content_layout.addWidget(toolbar_group)

        # -- Results Table --
        self.table_group = QGroupBox("Measurement Data Matrix", content)
        table_layout = QVBoxLayout(self.table_group)

        table_help = QLabel(
            "Enter response values directly in the editable cells below, or import from CSV. "
            "Leave blank if pending.",
            self.table_group,
        )
        table_help.setStyleSheet("color: #64748b; font-size: 12px; margin-bottom: 4px;")
        table_layout.addWidget(table_help)

        self.results_table = QTableWidget(0, 0, self.table_group)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.results_table.cellChanged.connect(self._on_cell_changed)
        table_layout.addWidget(self.results_table)

        self.validation_label = QLabel(self.table_group)
        self.validation_label.setStyleSheet("color: #dc2626; font-size: 12px; font-weight: 500;")
        table_layout.addWidget(self.validation_label)

        self._content_layout.addWidget(self.table_group)
        self._content_layout.addStretch(1)

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

    def _connect_signals(self) -> None:
        self.session.state_changed.connect(self._on_session_state_changed)

    # ------------------------------------------------------------------ #
    #  View Synchronization                                               #
    # ------------------------------------------------------------------ #

    def _on_session_state_changed(self) -> None:
        self._refresh_view()

    def _refresh_view(self) -> None:
        state = self.session.workflow_state
        exp = state.experiment if state else None
        design = state.design if state else None
        results = state.results if state else None

        if design is None or exp is None:
            self.status_badge.setText("No Design")
            self.status_badge.setStyleSheet("background-color: #94a3b8; color: white; padding: 4px 10px; border-radius: 4px;")
            self.status_text_label.setText("<b>No Design Available:</b> Please generate a design in the <i>Design</i> section first.")
            self.export_template_btn.setEnabled(False)
            self.import_csv_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            self.clear_btn.setEnabled(False)
            self.results_table.setEnabled(False)
            self.results_table.setRowCount(0)
            return

        self.export_template_btn.setEnabled(True)
        self.import_csv_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.clear_btn.setEnabled(results is not None and bool(results.entries))
        self.results_table.setEnabled(True)

        self._populate_table(design, exp, results)
        self._update_completeness_badge(design, exp, results)

    def _populate_table(self, design, exp, results) -> None:
        self._is_populating = True
        try:
            factor_names = [f.name for f in exp.factors]
            response_names = [r.name for r in exp.responses]
            headers = ["Run #", "Run ID"] + factor_names + response_names + ["Status"]

            self.results_table.setRowCount(len(design.runs))
            self.results_table.setColumnCount(len(headers))
            self.results_table.setHorizontalHeaderLabels(headers)

            results_map: Dict[str, ResultEntry] = {}
            if results and getattr(results, "entries", None):
                for e in results.entries:
                    results_map[e.run_ref] = e

            num_context_cols = 2 + len(factor_names)

            for row_idx, run in enumerate(design.runs):
                # 1. Run Number (Read-only)
                run_num_item = QTableWidgetItem(str(run.run_number or row_idx + 1))
                run_num_item.setFlags(run_num_item.flags() & ~Qt.ItemIsEditable)
                run_num_item.setBackground(Qt.lightGray)
                self.results_table.setItem(row_idx, 0, run_num_item)

                # 2. Run ID (Read-only)
                run_id_item = QTableWidgetItem(str(run.run_id))
                run_id_item.setFlags(run_id_item.flags() & ~Qt.ItemIsEditable)
                run_id_item.setBackground(Qt.lightGray)
                self.results_table.setItem(row_idx, 1, run_id_item)

                # 3. Factor values (Read-only)
                for f_idx, fname in enumerate(factor_names, start=2):
                    f_val = run.factor_values.get(fname, "")
                    f_item = QTableWidgetItem(str(f_val))
                    f_item.setFlags(f_item.flags() & ~Qt.ItemIsEditable)
                    f_item.setBackground(Qt.lightGray)
                    f_item.setTextAlignment(Qt.AlignCenter)
                    self.results_table.setItem(row_idx, f_idx, f_item)

                # 4. Response columns (Editable)
                entry = results_map.get(run.run_id)
                row_complete = True
                for r_idx, rname in enumerate(response_names, start=num_context_cols):
                    val_str = ""
                    if entry and isinstance(entry.values, dict) and rname in entry.values:
                        val_str = str(entry.values[rname])
                    else:
                        row_complete = False

                    r_item = QTableWidgetItem(val_str)
                    r_item.setTextAlignment(Qt.AlignCenter)
                    self.results_table.setItem(row_idx, r_idx, r_item)

                # 5. Status column (Read-only)
                status_col_idx = len(headers) - 1
                status_text = "Complete" if (entry and row_complete) else "Pending"
                status_item = QTableWidgetItem(status_text)
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                status_item.setTextAlignment(Qt.AlignCenter)
                if status_text == "Complete":
                    status_item.setForeground(Qt.darkGreen)
                else:
                    status_item.setForeground(Qt.darkRed)
                self.results_table.setItem(row_idx, status_col_idx, status_item)

        finally:
            self._is_populating = False

    def _update_completeness_badge(self, design, exp, results) -> None:
        total_runs = len(design.runs)
        recorded_runs = 0
        total_expected_measurements = total_runs * len(exp.responses)
        recorded_measurements = 0

        if results and getattr(results, "entries", None):
            for entry in results.entries:
                if isinstance(entry.values, dict):
                    valid_resps = sum(
                        1
                        for r in exp.responses
                        if r.name in entry.values
                        and isinstance(entry.values[r.name], (int, float))
                        and not isinstance(entry.values[r.name], bool)
                    )
                    recorded_measurements += valid_resps
                    if valid_resps == len(exp.responses) and entry.status == "complete":
                        recorded_runs += 1

        is_complete = recorded_runs == total_runs and total_runs > 0

        if is_complete:
            self.status_badge.setText("Results Complete")
            self.status_badge.setStyleSheet(
                "background-color: #16a34a; color: white; font-weight: bold; border-radius: 4px; padding: 4px 10px;"
            )
            self.status_text_label.setText(
                f"<b>All {total_runs} experimental runs completed.</b> "
                f"Ready for statistical regression modeling in the <i>Analysis</i> section."
            )
        elif recorded_runs > 0 or recorded_measurements > 0:
            self.status_badge.setText("In Progress (Partial)")
            self.status_badge.setStyleSheet(
                "background-color: #d97706; color: white; font-weight: bold; border-radius: 4px; padding: 4px 10px;"
            )
            missing = total_expected_measurements - recorded_measurements
            self.status_text_label.setText(
                f"<b>{recorded_runs} of {total_runs} runs complete.</b> "
                f"Recorded measurements: {recorded_measurements}/{total_expected_measurements} "
                f"({missing} missing)."
            )
        else:
            self.status_badge.setText("No Measurements")
            self.status_badge.setStyleSheet(
                "background-color: #64748b; color: white; font-weight: bold; border-radius: 4px; padding: 4px 10px;"
            )
            self.status_text_label.setText(
                f"<b>0 of {total_runs} runs recorded.</b> "
                f"Please input measured response values or import them from a CSV file."
            )

    def _on_cell_changed(self, row: int, col: int) -> None:
        if self._is_populating:
            return
        self.validation_label.clear()

    # ------------------------------------------------------------------ #
    #  Actions & Event Handlers                                          #
    # ------------------------------------------------------------------ #

    def _on_export_template(self) -> None:
        state = self.session.workflow_state
        if not state.design or not state.experiment:
            QMessageBox.warning(self, "No Design", "A design must be generated before exporting a results template.")
            return

        suggested = f"{state.experiment.name.replace(' ', '_')}_results_template.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results CSV Template",
            suggested,
            "CSV Files (*.csv);;All Files (*)",
        )
        if not file_path:
            return

        try:
            export_results_template_csv(state.design, state.experiment, file_path)
            QMessageBox.information(
                self,
                "Template Exported",
                f"Results template successfully saved to:\n{os.path.basename(file_path)}\n\n"
                f"Fill in experimental measurements and import the file when ready.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export template:\n\n{str(e)}")

    def _on_import_csv(self) -> None:
        state = self.session.workflow_state
        if not state.design or not state.experiment:
            QMessageBox.warning(self, "No Design", "A design must exist before importing results.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Experimental Results CSV",
            "",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not file_path:
            return

        try:
            entries = import_results_from_csv(
                file_path, design=state.design, responses=state.experiment.responses
            )
            new_state = insert_results(state, entries, audit_info={"source": "csv_import", "file": os.path.basename(file_path)})
            self.session.set_workflow_state(new_state, is_dirty=True)
            self.results_updated.emit()
            QMessageBox.information(
                self,
                "Import Successful",
                f"Successfully imported {len(entries)} result entries from:\n{os.path.basename(file_path)}",
            )
        except (DoeError, DomainValidationError) as e:
            QMessageBox.critical(self, "CSV Import Error", f"Failed to import results from CSV:\n\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "System Error", f"An unexpected error occurred during import:\n\n{str(e)}")

    def _on_save_results(self) -> None:
        state = self.session.workflow_state
        if not state.design or not state.experiment:
            return

        exp = state.experiment
        design = state.design
        factor_names = [f.name for f in exp.factors]
        response_names = [r.name for r in exp.responses]
        num_context_cols = 2 + len(factor_names)

        entries: List[ResultEntry] = []
        errors: List[str] = []

        for row_idx in range(self.results_table.rowCount()):
            run_id = self.results_table.item(row_idx, 1).text()
            run_num = self.results_table.item(row_idx, 0).text()

            values: Dict[str, float] = {}
            row_has_any = False
            row_complete = True

            for r_idx, rname in enumerate(response_names, start=num_context_cols):
                item = self.results_table.item(row_idx, r_idx)
                cell_text = item.text().strip() if item else ""
                if cell_text:
                    row_has_any = True
                    try:
                        numeric_val = float(cell_text)
                        if numeric_val.is_integer():
                            numeric_val = int(numeric_val)
                        values[rname] = numeric_val
                    except ValueError:
                        errors.append(f"Row {run_num} ({rname}): '{cell_text}' is not a valid number.")
                        row_complete = False
                else:
                    row_complete = False

            if row_has_any:
                status = "complete" if (row_complete and len(values) == len(response_names)) else "partial"
                entry = ResultEntry(run_ref=run_id, values=values, status=status)
                entries.append(entry)

        if errors:
            err_msg = "\n".join(errors[:10])
            if len(errors) > 10:
                err_msg += f"\n... and {len(errors) - 10} more errors."
            QMessageBox.warning(self, "Validation Error", f"Please correct the following errors:\n\n{err_msg}")
            return

        if not entries:
            QMessageBox.warning(self, "No Entries", "No response measurements were entered.")
            return

        try:
            new_state = insert_results(state, entries, audit_info={"source": "manual_entry"})
            self.session.set_workflow_state(new_state, is_dirty=True)
            self.results_updated.emit()
            QMessageBox.information(
                self,
                "Results Saved",
                f"Successfully committed {len(entries)} result entries.\n"
                f"Workflow status: {new_state.step.replace('_', ' ').title()}",
            )
        except (DoeError, DomainValidationError) as e:
            QMessageBox.critical(self, "Results Error", f"Failed to save results:\n\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "System Error", f"An unexpected error occurred:\n\n{str(e)}")

    def _on_clear_results(self) -> None:
        state = self.session.workflow_state
        if not state.results:
            return

        reply = QMessageBox.question(
            self,
            "Clear Results",
            "Are you sure you want to clear all experimental measurements?\n"
            "This will reset the workflow step back to 'Design Generated'.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        from doe.models import WorkflowState
        new_state = WorkflowState(
            step="design_generated",
            experiment=state.experiment,
            design=state.design,
            results=None,
            analysis=None,
            audit={"action": "clear_results"},
        )
        self.session.set_workflow_state(new_state, is_dirty=True)
        self.results_updated.emit()

