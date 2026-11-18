"""Full end-to-end integration test executing the complete 11-step DOE lifecycle through the GUI views."""
import os
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication, QMessageBox

from doe.gui.session import GuiSession
from doe.gui.main_window import MainWindow
from doe.models import Factor, Response, WorkflowState
from doe.designs.utils import export_design_to_csv, export_design_to_excel
from doe.result_input import export_results_template_csv
from doe.report_generation import generate_report


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(["-platform", "offscreen"])
    return app


@pytest.fixture(autouse=True)
def auto_mock_messagebox(monkeypatch):
    """Automatically bypass modal message boxes during headless tests."""
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: QMessageBox.Yes)
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)


def test_complete_e2e_gui_lifecycle(tmp_path, qapp):
    """Executes the complete 11-criteria Definition of Done workflow through GUI components."""

    # ------------------------------------------------------------------ #
    # Criterion 1 & 2: Create experiment, define factors and responses   #
    # ------------------------------------------------------------------ #
    session = GuiSession()
    window = MainWindow(session=session)

    exp_view = window.experiment_view
    exp_view.name_edit.setText("E2E GUI Optimization")
    exp_view.description_edit.setPlainText("Complete automated GUI lifecycle validation")

    f1 = Factor(name="temp", type="continuous", lower_bound=100.0, upper_bound=200.0, unit="°C")
    f2 = Factor(name="pressure", type="continuous", lower_bound=1.0, upper_bound=2.0, unit="bar")
    r1 = Response(name="yield", type="continuous", unit="%")

    exp_view._factors = [f1, f2]
    exp_view._responses = [r1]

    created = exp_view._on_create_experiment()
    assert created is True
    assert session.step == "experiment_created"
    assert session.is_dirty is True
    assert session.workflow_state.experiment.name == "E2E GUI Optimization"
    assert len(session.workflow_state.experiment.factors) == 2
    assert len(session.workflow_state.experiment.responses) == 1

    # ------------------------------------------------------------------ #
    # Criterion 3: Generate supported experimental design                #
    # ------------------------------------------------------------------ #
    window.nav_buttons[1].click()  # Switch to Design View
    assert window.stack.currentIndex() == 1
    design_view = window.design_view

    assert "4" in design_view.run_calc_label.text()

    design_view._on_generate_design()
    assert session.step == "design_generated"
    assert session.workflow_state.design is not None
    assert len(session.workflow_state.design.runs) == 4
    assert not design_view.inspection_group.isHidden()

    # ------------------------------------------------------------------ #
    # Criterion 4: Inspect and export the generated run table            #
    # ------------------------------------------------------------------ #
    assert design_view.run_table.rowCount() == 4
    assert design_view.coded_table.rowCount() == 4

    csv_design_path = str(tmp_path / "e2e_design.csv")
    export_design_to_csv(session.workflow_state.design, session.workflow_state.experiment, csv_design_path)
    assert os.path.exists(csv_design_path)
    with open(csv_design_path, encoding="utf-8") as f:
        csv_text = f.read()
    assert "Run Number,Run ID,temp,pressure" in csv_text

    excel_design_path = str(tmp_path / "e2e_design.xml")
    export_design_to_excel(session.workflow_state.design, session.workflow_state.experiment, excel_design_path)
    assert os.path.exists(excel_design_path)

    # ------------------------------------------------------------------ #
    # Criterion 5 & 6: Results entry, template export, completeness      #
    # ------------------------------------------------------------------ #
    window.nav_buttons[2].click()  # Switch to Results View
    assert window.stack.currentIndex() == 2
    results_view = window.results_view

    template_path = str(tmp_path / "e2e_template.csv")
    export_results_template_csv(session.workflow_state.design, session.workflow_state.experiment, template_path)
    assert os.path.exists(template_path)

    measurements = [35.2, 40.8, 55.4, 60.1]
    # Col index 4 is 'yield' (col 0: Run #, col 1: Run ID, col 2: temp, col 3: press, col 4: yield, col 5: Status)
    for row_idx, val in enumerate(measurements):
        results_view.results_table.item(row_idx, 4).setText(str(val))

    results_view._on_save_results()
    assert session.step == "results_complete"
    assert "Complete" in results_view.status_badge.text()
    assert len(session.workflow_state.results.entries) == 4

    # ------------------------------------------------------------------ #
    # Criterion 7 & 8: Execute statistical analysis & inspect outputs     #
    # ------------------------------------------------------------------ #
    window.nav_buttons[3].click()  # Switch to Analysis View
    assert window.stack.currentIndex() == 3
    analysis_view = window.analysis_view

    analysis_view.model_type_combo.setCurrentIndex(0)  # Linear model
    analysis_view.response_combo.setCurrentText("yield")

    analysis_view._on_run_analysis()
    assert session.step == "analysis_created"
    assert session.workflow_state.analysis is not None
    assert session.workflow_state.analysis.r_squared > 0.95
    assert not analysis_view.results_group.isHidden()
    assert analysis_view.coeffs_table.rowCount() == 3
    assert analysis_view.anova_table.rowCount() == 3
    assert analysis_view.residuals_table.rowCount() == 4

    # ------------------------------------------------------------------ #
    # Criterion 9 & 10: Generate, preview, and export Markdown report    #
    # ------------------------------------------------------------------ #
    window.nav_buttons[4].click()  # Switch to Report View
    assert window.stack.currentIndex() == 4
    report_view = window.report_view

    raw_markdown = report_view.raw_text_edit.toPlainText()
    assert "# Experiment Report: E2E GUI Optimization" in raw_markdown
    assert "## Statistical Analysis" in raw_markdown

    report_path = str(tmp_path / "e2e_final_report.md")
    new_state = generate_report(session.workflow_state, output_path=report_path, format="markdown")
    session.set_workflow_state(new_state)

    assert os.path.exists(report_path)
    assert session.step == "report_generated"

    # ------------------------------------------------------------------ #
    # Criterion 11: Save and reload workflow JSON without data loss      #
    # ------------------------------------------------------------------ #
    workflow_json_path = str(tmp_path / "e2e_final_workflow.json")
    session.save_to_file(workflow_json_path)
    assert os.path.exists(workflow_json_path)
    assert session.is_dirty is False

    reloaded_session = GuiSession()
    reloaded_window = MainWindow(session=reloaded_session)
    reloaded_session.load_from_file(workflow_json_path)

    assert reloaded_session.step == "report_generated"
    assert reloaded_session.workflow_state.experiment.name == "E2E GUI Optimization"
    assert len(reloaded_session.workflow_state.design.runs) == 4
    assert len(reloaded_session.workflow_state.results.entries) == 4
    assert reloaded_session.workflow_state.analysis.r_squared > 0.95

    assert reloaded_window.experiment_view.name_edit.text() == "E2E GUI Optimization"
    assert reloaded_window.design_view.run_table.rowCount() == 4
    assert reloaded_window.results_view.results_table.rowCount() == 4
    assert reloaded_window.analysis_view.coeffs_table.rowCount() == 3
    assert "# Experiment Report" in reloaded_window.report_view.raw_text_edit.toPlainText()
