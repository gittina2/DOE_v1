"""Functional Analysis view for statistical model selection, eligibility verification, OLS regression, ANOVA, and residual diagnostics."""
from typing import Dict, List, Optional, Tuple

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
    QAbstractItemView,
)

from doe.gui.session import GuiSession
from doe.analysis_computation import analyze_experiment
from doe.models import Analysis, DoeError, DomainValidationError
from doe.gui.styles import (
    get_header_style,
    get_formula_frame_style,
    get_primary_button_style,
    get_summary_card_style,
    get_eligibility_banner_style,
    colors,
)


class AnalysisView(QWidget):
    """Statistical regression modeling, eligibility verification, and ANOVA inspection view."""

    analysis_completed = Signal()

    MODEL_TYPES = [
        ("Linear Model (Main Effects)", "linear"),
        ("Interaction Model (Main Effects + 2-Way Interactions)", "interaction"),
        ("Quadratic Model (Main Effects + Squared Terms)", "quadratic"),
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
        header = QLabel("Statistical Analysis & Modeling", content)
        header.setStyleSheet(get_header_style())
        self._content_layout.addWidget(header)

        # -- Model Configuration Panel --
        self.config_group = QGroupBox("Model Specification & Eligibility", content)
        config_layout = QVBoxLayout(self.config_group)
        config_layout.setSpacing(12)

        # Response variable selection row
        resp_row = QHBoxLayout()
        resp_label = QLabel("Response Variable:", self.config_group)
        resp_label.setStyleSheet("font-weight: bold; min-width: 140px;")
        resp_row.addWidget(resp_label)

        self.response_combo = QComboBox(self.config_group)
        self.response_combo.currentIndexChanged.connect(self._on_spec_changed)
        resp_row.addWidget(self.response_combo, 1)
        config_layout.addLayout(resp_row)

        # Model type selection row
        type_row = QHBoxLayout()
        type_label = QLabel("Statistical Model:", self.config_group)
        type_label.setStyleSheet("font-weight: bold; min-width: 140px;")
        type_row.addWidget(type_label)

        self.model_type_combo = QComboBox(self.config_group)
        for label, val in self.MODEL_TYPES:
            self.model_type_combo.addItem(label, val)
        self.model_type_combo.currentIndexChanged.connect(self._on_spec_changed)
        type_row.addWidget(self.model_type_combo, 1)
        config_layout.addLayout(type_row)

        # Formula Preview Frame
        self.formula_frame = QFrame(self.config_group)
        self.formula_frame.setObjectName("formulaFrame")
        self.formula_frame.setStyleSheet(get_formula_frame_style())
        formula_layout = QHBoxLayout(self.formula_frame)
        formula_layout.setContentsMargins(4, 4, 4, 4)
        formula_hdr = QLabel("Formula Preview:", self.formula_frame)
        formula_hdr.setStyleSheet(f"font-weight: bold; color: {colors.FORMULA_HDR_TEXT}; min-width: 130px;")
        formula_layout.addWidget(formula_hdr)

        self.formula_label = QLabel(self.formula_frame)
        self.formula_label.setStyleSheet(f"font-family: monospace; font-size: 13px; color: {colors.FORMULA_TEXT};")
        formula_layout.addWidget(self.formula_label, 1)
        config_layout.addWidget(self.formula_frame)

        # Eligibility & Estimability Banner
        self.eligibility_frame = QFrame(self.config_group)
        elig_layout = QHBoxLayout(self.eligibility_frame)
        elig_layout.setContentsMargins(10, 8, 10, 8)
        self.eligibility_label = QLabel(self.eligibility_frame)
        self.eligibility_label.setWordWrap(True)
        elig_layout.addWidget(self.eligibility_label)
        config_layout.addWidget(self.eligibility_frame)

        # Run Analysis Action Button
        run_btn_layout = QHBoxLayout()
        run_btn_layout.addStretch(1)
        self.run_btn = QPushButton("Run Analysis", self.config_group)
        self.run_btn.setMinimumHeight(38)
        self.run_btn.setMinimumWidth(200)
        self.run_btn.setStyleSheet(
            get_primary_button_style(
                font_size="14px",
                padding="8px 24px",
                border_radius="6px",
                include_disabled=True,
            )
        )
        self.run_btn.clicked.connect(self._on_run_analysis)
        run_btn_layout.addWidget(self.run_btn)
        run_btn_layout.addStretch(1)
        config_layout.addLayout(run_btn_layout)

        self._content_layout.addWidget(self.config_group)

        # -- Results Presentation (Tabbed Widget) --
        self.results_group = QGroupBox("Model Outputs & Diagnostics", content)
        results_layout = QVBoxLayout(self.results_group)

        self.tabs = QTabWidget(self.results_group)

        # Tab 1: Summary Cards
        self.summary_tab = QWidget()
        summary_tab_layout = QVBoxLayout(self.summary_tab)
        self.summary_card = QFrame(self.summary_tab)
        self.summary_card.setObjectName("summaryCard")
        self.summary_card.setStyleSheet(get_summary_card_style())
        card_layout = QVBoxLayout(self.summary_card)
        self.summary_card_label = QLabel(self.summary_card)
        self.summary_card_label.setTextFormat(Qt.RichText)
        self.summary_card_label.setStyleSheet(f"font-size: 13px; line-height: 1.6; color: {colors.OVERVIEW_TEXT};")
        card_layout.addWidget(self.summary_card_label)
        summary_tab_layout.addWidget(self.summary_card)
        summary_tab_layout.addStretch(1)
        self.tabs.addTab(self.summary_tab, "Summary & Fit Statistics")

        # Tab 2: Coefficients Table
        self.coeffs_table = QTableWidget(0, 5, self.tabs)
        self.coeffs_table.setHorizontalHeaderLabels(["Term", "Estimate (β̂)", "p-Value", "Significance", "Coded Space"])
        self.coeffs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.coeffs_table.setAlternatingRowColors(True)
        self.coeffs_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabs.addTab(self.coeffs_table, "Regression Coefficients")

        # Tab 3: ANOVA Table
        self.anova_table = QTableWidget(0, 6, self.tabs)
        self.anova_table.setHorizontalHeaderLabels(["Source", "Sum of Squares (SS)", "DF", "Mean Square (MS)", "F-Value", "p-Value"])
        self.anova_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.anova_table.setAlternatingRowColors(True)
        self.anova_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabs.addTab(self.anova_table, "ANOVA Table")

        # Tab 4: Residuals Table
        self.residuals_table = QTableWidget(0, 4, self.tabs)
        self.residuals_table.setHorizontalHeaderLabels(["Run #", "Observed (Y)", "Fitted (Ŷ)", "Residual (e = Y - Ŷ)"])
        self.residuals_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.residuals_table.setAlternatingRowColors(True)
        self.residuals_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabs.addTab(self.residuals_table, "Residual Diagnostics")

        results_layout.addWidget(self.tabs)
        self._content_layout.addWidget(self.results_group)
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

    def _on_spec_changed(self) -> None:
        self._update_eligibility()

    def _refresh_view(self) -> None:
        state = self.session.workflow_state
        exp = state.experiment if state else None
        design = state.design if state else None
        results = state.results if state else None
        analysis = state.analysis if state else None

        # Populate response combo box without triggering multiple signals
        self.response_combo.blockSignals(True)
        current_resp = self.response_combo.currentText()
        self.response_combo.clear()

        if exp and exp.responses:
            for r in exp.responses:
                self.response_combo.addItem(r.name)
            # Restore selection if possible
            idx = self.response_combo.findText(current_resp)
            if idx >= 0:
                self.response_combo.setCurrentIndex(idx)
        self.response_combo.blockSignals(False)

        self._update_eligibility()

        if analysis is not None:
            self._populate_analysis_outputs(analysis, exp, design, results)
            self.results_group.setVisible(True)
        else:
            self.results_group.setVisible(False)

    def _check_model_eligibility(self) -> Tuple[bool, str, str, str]:
        """Verify mathematical eligibility of the selected model.

        Returns: (is_eligible, message, style_color, background_color)
        """
        state = self.session.workflow_state
        exp = state.experiment if state else None
        design = state.design if state else None
        results = state.results if state else None

        if not exp or not design:
            return (
                False,
                "<b>No Experimental Design:</b> Please generate a design in the <i>Design</i> section first.",
                colors.WARNING_BORDER,
                colors.WARNING_BG,
            )

        if not results or getattr(results, "completeness", "") != "complete":
            recorded = len(results.entries) if results and results.entries else 0
            total = len(design.runs)
            return (
                False,
                f"<b>Incomplete Results:</b> Regression modeling requires all runs to be recorded. "
                f"Current progress: {recorded} of {total} runs complete. Please record all responses in the <i>Results</i> section.",
                colors.WARNING_BORDER,
                colors.WARNING_BG,
            )

        model_type = self.model_type_combo.currentData()
        N = len(design.runs)
        k = len(exp.factors)

        # 1. Quadratic Model Check
        if model_type == "quadratic":
            has_insufficient_levels = False
            for f in exp.factors:
                f_type = f.type.value if hasattr(f.type, "value") else str(f.type)
                if f_type == "continuous":
                    levels_in_design = {run.factor_values.get(f.name) for run in design.runs}
                    if len(levels_in_design) < 3:
                        has_insufficient_levels = True
                        break

            if has_insufficient_levels:
                return (
                    False,
                    "<b>Non-Estimable Model (Quadratic):</b> Quadratic models require at least 3 distinct levels "
                    "per continuous factor (such as center points). The current 2-level factorial design matrix is "
                    "rank-deficient for quadratic terms.",
                    colors.BLOCKED_BORDER,
                    colors.BLOCKED_BG,
                )

        # 2. Interaction Model Degrees of Freedom Check
        if model_type == "interaction":
            num_params = 1 + k + (k * (k - 1) // 2)
            if N <= num_params:
                return (
                    False,
                    f"<b>Insufficient Observations:</b> The interaction model requires {num_params} parameters, "
                    f"but the design only contains {N} runs ($N ≤ p$). At least {num_params + 1} runs are required "
                    f"to have residual degrees of freedom.",
                    colors.BLOCKED_BORDER,
                    colors.BLOCKED_BG,
                )

        # 3. Linear Model Check
        if model_type == "linear":
            num_params = 1 + k
            if N <= num_params:
                return (
                    False,
                    f"<b>Insufficient Observations:</b> Linear model requires {num_params} parameters, "
                    f"but only {N} runs are available ($N ≤ p$).",
                    colors.BLOCKED_BORDER,
                    colors.BLOCKED_BG,
                )

        # Eligible
        p_est = 1 + k if model_type == "linear" else (1 + k + (k * (k - 1) // 2) if model_type == "interaction" else 1 + 2 * k)
        df_res = N - p_est
        return (
            True,
            f"<b>Model Estimable:</b> Design and data satisfy all mathematical requirements "
            f"($N = {N}$ observations, $p = {p_est}$ terms, $df_{{\\text{{res}}}} = {df_res}$).",
            colors.ELIGIBLE_BORDER,
            colors.ELIGIBLE_BG,
        )

    def _update_eligibility(self) -> None:
        state = self.session.workflow_state
        exp = state.experiment if state else None
        selected_resp = self.response_combo.currentText() or (exp.responses[0].name if exp and exp.responses else "Y")
        model_type = self.model_type_combo.currentData() or "linear"

        # Update formula preview
        if exp and exp.factors:
            main_terms = [f.name for f in exp.factors]
            if model_type == "linear":
                terms = main_terms
            elif model_type == "interaction":
                int_terms = [f"{main_terms[i]}:{main_terms[j]}" for i in range(len(main_terms)) for j in range(i + 1, len(main_terms))]
                terms = main_terms + int_terms
            else:  # quadratic
                quad_terms = [f"{name}²" for name in main_terms]
                terms = main_terms + quad_terms
            formula_text = f"{selected_resp} ~ 1 + {' + '.join(terms)}"
        else:
            formula_text = f"{selected_resp} ~ 1 + factors..."

        self.formula_label.setText(formula_text)

        is_eligible, message, text_color, bg_color = self._check_model_eligibility()
        self.eligibility_frame.setStyleSheet(get_eligibility_banner_style(bg_color, text_color))
        self.eligibility_label.setStyleSheet(f"color: {text_color}; font-size: 13px;")
        self.eligibility_label.setText(message)
        self.run_btn.setEnabled(is_eligible)

    def _populate_analysis_outputs(self, analysis: Analysis, exp, design, results) -> None:
        # 1. Summary Card
        r2_str = f"{analysis.r_squared:.4f}" if analysis.r_squared is not None else "N/A"
        adj_r2_str = f"{analysis.adjusted_r_squared:.4f}" if analysis.adjusted_r_squared is not None else "N/A"
        n_obs = analysis.diagnostics.get("n_observations", len(analysis.residuals) if analysis.residuals else "N/A")
        n_params = analysis.diagnostics.get("n_parameters", len(analysis.coefficients) if analysis.coefficients else "N/A")
        df_res = n_obs - n_params if isinstance(n_obs, int) and isinstance(n_params, int) else "N/A"

        card_lines = [
            f"<b>Analysis ID:</b> <code>{analysis.analysis_id}</code>",
            f"<b>Response Variable:</b> <b>{analysis.diagnostics.get('response_variable', 'Primary')}</b>",
            f"<b>Statistical Model:</b> {analysis.model_type.capitalize()} Model",
            f"<b>Model Formula:</b> <code>{analysis.formula}</code>",
            "<hr>",
            f"<b>R² (Coefficient of Determination):</b> <b>{r2_str}</b>",
            f"<b>Adjusted R²:</b> <b>{adj_r2_str}</b>",
            f"<b>Observations (N):</b> {n_obs} &nbsp;|&nbsp; <b>Model Parameters (p):</b> {n_params} &nbsp;|&nbsp; <b>Residual DF:</b> {df_res}",
        ]
        self.summary_card_label.setText("<br>".join(card_lines))

        # 2. Coefficients Table
        coeffs = analysis.coefficients or {}
        p_vals = analysis.p_values or {}
        self.coeffs_table.setRowCount(len(coeffs))

        for row_idx, (term, est) in enumerate(coeffs.items()):
            p_val = p_vals.get(term)
            p_str = f"{p_val:.4f}" if p_val is not None else "N/A"
            sig_text = "Significant (p < 0.05)" if (p_val is not None and p_val < 0.05) else "Not Significant"

            term_item = QTableWidgetItem(term)
            est_item = QTableWidgetItem(f"{est:+.4f}")
            est_item.setTextAlignment(Qt.AlignCenter)

            p_item = QTableWidgetItem(p_str)
            p_item.setTextAlignment(Qt.AlignCenter)

            sig_item = QTableWidgetItem(sig_text)
            sig_item.setTextAlignment(Qt.AlignCenter)
            if p_val is not None and p_val < 0.05:
                sig_item.setForeground(colors.TABLE_SIG_TERM_FG)
                term_item.setFont(self.font())
                term_item.setBackground(colors.TABLE_SIG_TERM_BG if term != "Intercept" else colors.TABLE_WHITE_BG)
            else:
                sig_item.setForeground(colors.TABLE_NONSIG_TERM_FG)

            coded_item = QTableWidgetItem("Yes" if term != "Intercept" else "-")
            coded_item.setTextAlignment(Qt.AlignCenter)

            self.coeffs_table.setItem(row_idx, 0, term_item)
            self.coeffs_table.setItem(row_idx, 1, est_item)
            self.coeffs_table.setItem(row_idx, 2, p_item)
            self.coeffs_table.setItem(row_idx, 3, sig_item)
            self.coeffs_table.setItem(row_idx, 4, coded_item)

        # 3. ANOVA Table
        anova_rows = analysis.anova_table or []
        self.anova_table.setRowCount(len(anova_rows))

        for row_idx, row_dict in enumerate(anova_rows):
            source = row_dict.get("source", "")
            ss_val = row_dict.get("ss")
            df_val = row_dict.get("df")
            ms_val = row_dict.get("ms")
            f_val = row_dict.get("f_value")
            p_val = row_dict.get("p_value")

            ss_str = f"{ss_val:.4f}" if ss_val is not None else "N/A"
            df_str = str(df_val) if df_val is not None else "N/A"
            ms_str = f"{ms_val:.4f}" if ms_val is not None else "N/A"
            f_str = f"{f_val:.4f}" if f_val is not None else "N/A"
            p_str = f"{p_val:.4f}" if p_val is not None else "N/A"

            src_item = QTableWidgetItem(source)
            src_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.anova_table.setItem(row_idx, 0, src_item)

            for col_idx, text in enumerate([ss_str, df_str, ms_str, f_str, p_str], start=1):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                self.anova_table.setItem(row_idx, col_idx, item)

        # 4. Residuals Table
        residuals = analysis.residuals or []
        resp_name = analysis.diagnostics.get("response_variable")
        self.residuals_table.setRowCount(len(residuals))

        results_by_run = {e.run_ref: e for e in results.entries} if results and results.entries else {}

        for row_idx, res_val in enumerate(residuals):
            run = design.runs[row_idx] if design and row_idx < len(design.runs) else None
            entry = results_by_run.get(run.run_id) if run else None
            obs_y = entry.values.get(resp_name, "N/A") if entry and isinstance(entry.values, dict) else "N/A"

            if isinstance(obs_y, (int, float)):
                fitted_y = obs_y - res_val
                fitted_str = f"{fitted_y:.4f}"
                obs_str = f"{obs_y:.4f}"
            else:
                fitted_str = "N/A"
                obs_str = str(obs_y)

            run_num_str = str(run.run_number or row_idx + 1) if run else str(row_idx + 1)

            self.residuals_table.setItem(row_idx, 0, QTableWidgetItem(run_num_str))
            self.residuals_table.setItem(row_idx, 1, QTableWidgetItem(obs_str))
            self.residuals_table.setItem(row_idx, 2, QTableWidgetItem(fitted_str))

            res_item = QTableWidgetItem(f"{res_val:+.4f}")
            res_item.setTextAlignment(Qt.AlignCenter)
            self.residuals_table.setItem(row_idx, 3, res_item)

    # ------------------------------------------------------------------ #
    #  Actions                                                            #
    # ------------------------------------------------------------------ #

    def _on_run_analysis(self) -> None:
        state = self.session.workflow_state
        if state.step != "results_complete":
            QMessageBox.warning(self, "Incomplete Results", "All experimental results must be recorded before running analysis.")
            return

        selected_resp = self.response_combo.currentText()
        selected_model = self.model_type_combo.currentData()

        try:
            new_state = analyze_experiment(
                state, model_type=selected_model, response_name=selected_resp
            )
            self.session.set_workflow_state(new_state, is_dirty=True)
            self.analysis_completed.emit()
            QMessageBox.information(
                self,
                "Analysis Complete",
                f"Statistical {selected_model} model fitted successfully for response '{selected_resp}'.\n\n"
                f"R² = {new_state.analysis.r_squared:.4f}\n"
                f"Adjusted R² = {new_state.analysis.adjusted_r_squared:.4f}",
            )
        except (DoeError, DomainValidationError) as e:
            QMessageBox.critical(self, "Analysis Error", f"Statistical computation failed:\n\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "System Error", f"An unexpected error occurred:\n\n{str(e)}")

