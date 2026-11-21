"""Functional Design view for configuring, generating, inspecting, and exporting experimental designs."""
import os
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QMessageBox,
    QScrollArea,
    QFrame,
    QTabWidget,
    QFileDialog,
    QAbstractItemView,
    QCheckBox,
)

from doe.gui.session import GuiSession
from doe.design_generation import generate_design
from doe.designs.utils import export_design_to_csv, export_design_to_excel
from doe.models import DoeError, DomainValidationError, Design
from doe.gui.styles import (
    get_header_style,
    get_context_frame_style,
    get_calc_frame_style,
    get_primary_button_style,
    colors,
)


class DesignView(QWidget):
    """Full design configuration, run matrix inspection, and export view."""

    design_generated = Signal()

    DESIGN_TYPES = [
        ("Full Factorial (2-level / multi-level categorical)", "full_factorial"),
        ("Fractional Factorial (Half-Fraction 2^(k-1))", "fractional_factorial"),
    ]

    def __init__(self, session: GuiSession, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.session = session

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
        header = QLabel("Experimental Design", content)
        header.setStyleSheet(get_header_style())
        self._content_layout.addWidget(header)

        # -- Experiment Context Banner --
        self.context_frame = QFrame(content)
        self.context_frame.setObjectName("contextFrame")
        self.context_frame.setStyleSheet(get_context_frame_style())
        context_layout = QVBoxLayout(self.context_frame)
        context_layout.setContentsMargins(8, 8, 8, 8)
        self.context_label = QLabel(self.context_frame)
        self.context_label.setTextFormat(Qt.RichText)
        self.context_label.setStyleSheet(f"font-size: 13px; color: {colors.OVERVIEW_TEXT};")
        context_layout.addWidget(self.context_label)
        self._content_layout.addWidget(self.context_frame)

        # -- Design Configuration Group --
        self.config_group = QGroupBox("Design Strategy & Configuration", content)
        config_layout = QVBoxLayout(self.config_group)
        config_layout.setSpacing(12)

        # Design type selector
        type_row = QHBoxLayout()
        type_label = QLabel("Design Type:", self.config_group)
        type_label.setStyleSheet("font-weight: bold; min-width: 110px;")
        type_row.addWidget(type_label)

        self.design_type_combo = QComboBox(self.config_group)
        for label, val in self.DESIGN_TYPES:
            self.design_type_combo.addItem(label, val)
        self.design_type_combo.currentIndexChanged.connect(self._on_design_type_changed)
        type_row.addWidget(self.design_type_combo, 1)
        config_layout.addLayout(type_row)

        # Run count calculator preview banner
        self.run_calc_frame = QFrame(self.config_group)
        self.run_calc_frame.setObjectName("calcFrame")
        self.run_calc_frame.setStyleSheet(get_calc_frame_style())
        calc_layout = QHBoxLayout(self.run_calc_frame)
        calc_layout.setContentsMargins(4, 4, 4, 4)
        self.run_calc_label = QLabel(self.run_calc_frame)
        self.run_calc_label.setStyleSheet(f"color: {colors.CALC_FRAME_TEXT}; font-size: 13px;")
        calc_layout.addWidget(self.run_calc_label)
        config_layout.addWidget(self.run_calc_frame)

        # Advanced options notice (disabled controls with tooltips)
        adv_group = QGroupBox("Advanced Options (Roadmap / Future Features)", self.config_group)
        adv_layout = QHBoxLayout(adv_group)
        self.chk_randomize = QCheckBox("Randomize Runs", adv_group)
        self.chk_randomize.setEnabled(False)
        self.chk_randomize.setToolTip("Run sequence randomization is planned for a future core release.")
        adv_layout.addWidget(self.chk_randomize)

        self.chk_replicates = QCheckBox("Replication", adv_group)
        self.chk_replicates.setEnabled(False)
        self.chk_replicates.setToolTip("Design replication is planned for a future core release.")
        adv_layout.addWidget(self.chk_replicates)

        self.chk_center = QCheckBox("Center Points", adv_group)
        self.chk_center.setEnabled(False)
        self.chk_center.setToolTip("Center point generation is planned for a future core release.")
        adv_layout.addWidget(self.chk_center)

        self.chk_blocking = QCheckBox("Blocking", adv_group)
        self.chk_blocking.setEnabled(False)
        self.chk_blocking.setToolTip("Experimental blocking is planned for a future core release.")
        adv_layout.addWidget(self.chk_blocking)

        config_layout.addWidget(adv_group)

        # Generate action button
        gen_btn_layout = QHBoxLayout()
        gen_btn_layout.addStretch(1)
        self.generate_btn = QPushButton("Generate Design", self.config_group)
        self.generate_btn.setMinimumHeight(38)
        self.generate_btn.setMinimumWidth(200)
        self.generate_btn.setStyleSheet(
            get_primary_button_style(
                font_size="14px",
                padding="8px 24px",
                border_radius="6px",
                include_disabled=True,
            )
        )
        self.generate_btn.clicked.connect(self._on_generate_design)
        gen_btn_layout.addWidget(self.generate_btn)
        gen_btn_layout.addStretch(1)
        config_layout.addLayout(gen_btn_layout)

        self._content_layout.addWidget(self.config_group)

        # -- Generated Design Inspection & Export Group --
        self.inspection_group = QGroupBox("Generated Design Matrix", content)
        inspection_layout = QVBoxLayout(self.inspection_group)
        inspection_layout.setSpacing(10)

        # Export buttons toolbar
        export_row = QHBoxLayout()
        export_label = QLabel("Export Run Table:", self.inspection_group)
        export_label.setStyleSheet("font-weight: bold;")
        export_row.addWidget(export_label)

        self.export_csv_btn = QPushButton("Export Design (CSV)...", self.inspection_group)
        self.export_csv_btn.clicked.connect(self._on_export_csv)
        export_row.addWidget(self.export_csv_btn)

        self.export_excel_btn = QPushButton("Export Design (Excel)...", self.inspection_group)
        self.export_excel_btn.clicked.connect(self._on_export_excel)
        export_row.addWidget(self.export_excel_btn)

        export_row.addStretch(1)
        inspection_layout.addLayout(export_row)

        # Tabbed tables: Experimental runs vs Coded levels
        self.tabs = QTabWidget(self.inspection_group)

        # Tab 1: Experimental runs
        self.run_table = QTableWidget(0, 0, self.tabs)
        self.run_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.run_table.setAlternatingRowColors(True)
        self.run_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tabs.addTab(self.run_table, "Experimental Runs (Natural Values)")

        # Tab 2: Coded levels
        self.coded_table = QTableWidget(0, 0, self.tabs)
        self.coded_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.coded_table.setAlternatingRowColors(True)
        self.coded_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tabs.addTab(self.coded_table, "Coded Levels ([-1.0, +1.0])")

        # Tab 3: Design metadata
        self.meta_frame = QFrame(self.tabs)
        meta_layout = QVBoxLayout(self.meta_frame)
        self.meta_label = QLabel(self.meta_frame)
        self.meta_label.setTextFormat(Qt.RichText)
        self.meta_label.setStyleSheet("font-size: 13px; line-height: 1.5;")
        meta_layout.addWidget(self.meta_label)
        meta_layout.addStretch(1)
        self.tabs.addTab(self.meta_frame, "Design Metadata")

        inspection_layout.addWidget(self.tabs)
        self._content_layout.addWidget(self.inspection_group)

        self._content_layout.addStretch(1)

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

    def _connect_signals(self) -> None:
        self.session.state_changed.connect(self._on_session_state_changed)

    # ------------------------------------------------------------------ #
    #  UI State & Refresh                                                 #
    # ------------------------------------------------------------------ #

    def _on_session_state_changed(self) -> None:
        self._refresh_view()

    def _on_design_type_changed(self) -> None:
        self._update_run_calculation()

    def _refresh_view(self) -> None:
        state = self.session.workflow_state
        exp = state.experiment if state else None
        design = state.design if state else None

        if exp is None:
            self.context_label.setText(
                "<b>No Experiment Defined:</b> Please create an experiment in the <i>Experiment</i> section first."
            )
            self.config_group.setEnabled(False)
            self.generate_btn.setEnabled(False)
            self.inspection_group.setVisible(False)
            self.run_calc_label.setText("Run count calculator will update once an experiment is created.")
            return

        self.config_group.setEnabled(True)
        self.generate_btn.setEnabled(True)

        # Populate context banner
        factor_summary = f"{len(exp.factors)} factor{'s' if len(exp.factors) != 1 else ''}"
        response_summary = f"{len(exp.responses)} response{'s' if len(exp.responses) != 1 else ''}"
        self.context_label.setText(
            f"<b>Active Experiment:</b> {exp.name} &nbsp;|&nbsp; <b>Setup:</b> {factor_summary}, {response_summary}"
        )

        self._update_run_calculation()

        if design is not None:
            self._populate_design_tables(design, exp)
            self.inspection_group.setVisible(True)
        else:
            self.inspection_group.setVisible(False)

    def _update_run_calculation(self) -> None:
        state = self.session.workflow_state
        exp = state.experiment if state else None
        if not exp or not exp.factors:
            self.run_calc_label.setText("At least one factor is required to calculate runs.")
            return

        design_type = self.design_type_combo.currentData()
        k = len(exp.factors)

        # Full factorial expected runs: 2^continuous * product(len(levels))
        full_runs = 1
        for f in exp.factors:
            if f.type == "categorical" and f.levels:
                full_runs *= len(f.levels)
            else:
                full_runs *= 2

        if design_type == "full_factorial":
            self.run_calc_label.setText(
                f"<b>Expected Runs:</b> <b>{full_runs}</b> runs "
                f"(Evaluates full factorial Cartesian product across all factor levels)."
            )
        elif design_type == "fractional_factorial":
            if k >= 3:
                frac_runs = 2 ** (k - 1)
                self.run_calc_label.setText(
                    f"<b>Expected Runs:</b> <b>{frac_runs}</b> runs "
                    f"(Half-fraction 2^({k}-1) subset based on parity relation; full factorial would be {full_runs})."
                )
            else:
                self.run_calc_label.setText(
                    f"<b>Expected Runs:</b> <b>{full_runs}</b> runs "
                    f"(Note: Fractional factorial requires k ≥ 3 factors; with {k} factor(s) it falls back to full factorial)."
                )

    def _populate_design_tables(self, design: Design, exp) -> None:
        factor_names = [f.name for f in exp.factors]

        # 1. Experimental Run Table
        headers = ["Run #", "Run ID"] + factor_names
        self.run_table.setRowCount(len(design.runs))
        self.run_table.setColumnCount(len(headers))
        self.run_table.setHorizontalHeaderLabels(headers)

        for row_idx, run in enumerate(design.runs):
            self.run_table.setItem(row_idx, 0, QTableWidgetItem(str(run.run_number or row_idx + 1)))
            self.run_table.setItem(row_idx, 1, QTableWidgetItem(str(run.run_id)))
            for col_idx, fname in enumerate(factor_names, start=2):
                val = run.factor_values.get(fname, "")
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                self.run_table.setItem(row_idx, col_idx, item)

        # 2. Coded Table
        self.coded_table.setRowCount(len(design.runs))
        self.coded_table.setColumnCount(len(headers))
        self.coded_table.setHorizontalHeaderLabels(headers)

        for row_idx, run in enumerate(design.runs):
            self.coded_table.setItem(row_idx, 0, QTableWidgetItem(str(run.run_number or row_idx + 1)))
            self.coded_table.setItem(row_idx, 1, QTableWidgetItem(str(run.run_id)))
            for col_idx, fname in enumerate(factor_names, start=2):
                val = run.factor_values.get(fname, "")
                if design.is_factor_coded(fname):
                    try:
                        coded_val = design.get_coded_value(fname, val)
                        coded_str = f"{coded_val:+.1f}" if coded_val in (-1.0, 1.0, 0.0) else f"{coded_val:+.3f}"
                    except Exception:
                        coded_str = str(val)
                else:
                    coded_str = str(val)

                item = QTableWidgetItem(coded_str)
                item.setTextAlignment(Qt.AlignCenter)
                self.coded_table.setItem(row_idx, col_idx, item)

        # 3. Metadata Tab
        meta_lines = [
            f"<b>Design ID:</b> <code>{design.design_id}</code>",
            f"<b>Experiment Reference:</b> <code>{design.experiment_ref}</code>",
            f"<b>Design Type:</b> {design.design_type}",
            f"<b>Total Experimental Runs:</b> {len(design.runs)}",
            f"<b>Randomization:</b> {'Yes' if design.randomization else 'No (Standard run order)'}",
            f"<b>Replications:</b> {design.replications or 1}",
            f"<b>Blocks:</b> {len(design.blocks) if design.blocks else 'None'}",
            f"<b>Factor Coding Count:</b> {len(design.factor_coding) if design.factor_coding else 0}",
        ]
        self.meta_label.setText("<br>".join(meta_lines))

    # ------------------------------------------------------------------ #
    #  Design Generation & Export Actions                                #
    # ------------------------------------------------------------------ #

    def _on_generate_design(self) -> None:
        state = self.session.workflow_state
        if state.experiment is None:
            QMessageBox.warning(self, "No Experiment", "Please define and create an experiment first.")
            return

        has_downstream = state.results is not None or state.analysis is not None
        if has_downstream or state.design is not None:
            msg = (
                "Regenerating the design will reset existing experimental results and statistical analysis.\n\n"
                "Do you want to continue?"
                if has_downstream
                else "A design already exists. Do you want to regenerate it?"
            )
            reply = QMessageBox.warning(
                self,
                "Confirm Design Generation",
                msg,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        # Prepare state for design generation: if in a later step, reset step to experiment_created
        if state.step != "experiment_created":
            # Reconstruct clean experiment_created state preserving experiment
            from doe.models import WorkflowState
            state = WorkflowState(
                step="experiment_created",
                experiment=state.experiment,
                audit={"action": "reset_for_design_generation"},
            )

        selected_type = self.design_type_combo.currentData()
        try:
            new_state = generate_design(state, design_type=selected_type)
            self.session.set_workflow_state(new_state, is_dirty=True)
            self.design_generated.emit()
            QMessageBox.information(
                self,
                "Design Generated",
                f"Successfully generated {len(new_state.design.runs)} experimental runs "
                f"using '{selected_type}'.",
            )
        except (DomainValidationError, DoeError) as e:
            QMessageBox.critical(self, "Design Generation Error", f"Failed to generate design:\n\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "System Error", f"An unexpected error occurred:\n\n{str(e)}")

    def _on_export_csv(self) -> None:
        state = self.session.workflow_state
        if not state.design:
            QMessageBox.warning(self, "No Design", "No design runs are available to export.")
            return

        suggested = f"{state.experiment.name.replace(' ', '_')}_design.csv" if state.experiment else "design.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Design Matrix to CSV",
            suggested,
            "CSV Files (*.csv);;All Files (*)",
        )
        if not file_path:
            return

        try:
            export_design_to_csv(state.design, state.experiment, file_path)
            QMessageBox.information(
                self,
                "Export Complete",
                f"Design matrix successfully exported to:\n{os.path.basename(file_path)}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export design CSV:\n\n{str(e)}")

    def _on_export_excel(self) -> None:
        state = self.session.workflow_state
        if not state.design:
            QMessageBox.warning(self, "No Design", "No design runs are available to export.")
            return

        suggested = f"{state.experiment.name.replace(' ', '_')}_design.xml" if state.experiment else "design.xml"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Design Matrix to Excel",
            suggested,
            "Excel Spreadsheet (*.xml *.xlsx *.xls);;All Files (*)",
        )
        if not file_path:
            return

        try:
            export_design_to_excel(state.design, state.experiment, file_path)
            QMessageBox.information(
                self,
                "Export Complete",
                f"Design matrix successfully exported to:\n{os.path.basename(file_path)}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export design spreadsheet:\n\n{str(e)}")

