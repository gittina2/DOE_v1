"""Unit tests for the ReportView GUI component."""
import os
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication, QMessageBox

from doe.gui.session import GuiSession
from doe.gui.views.report_view import ReportView
from doe.experiment_creation import create_experiment
from doe.design_generation import generate_design
from doe.result_input import insert_results
from doe.analysis_computation import analyze_experiment
from doe.models import Factor, Response, ResultEntry


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


@pytest.fixture
def analyzed_session():
    session = GuiSession()
    f1 = Factor(name="temp", type="continuous", lower_bound=100.0, upper_bound=200.0)
    f2 = Factor(name="press", type="continuous", lower_bound=1.0, upper_bound=2.0)
    r1 = Response(name="yield", type="continuous", unit="%")
    state = create_experiment(name="Report Test Exp", factors=[f1, f2], responses=[r1])
    state = generate_design(state)

    runs = state.design.runs
    entries = [
        ResultEntry(run_ref=runs[0].run_id, values={"yield": 35.5}),
        ResultEntry(run_ref=runs[1].run_id, values={"yield": 40.2}),
        ResultEntry(run_ref=runs[2].run_id, values={"yield": 55.8}),
        ResultEntry(run_ref=runs[3].run_id, values={"yield": 60.1}),
    ]
    state = insert_results(state, entries)
    state = analyze_experiment(state, model_type="linear")
    session.set_workflow_state(state, is_dirty=False)
    return session


def test_report_view_without_experiment(qapp):
    session = GuiSession()
    view = ReportView(session=session)
    assert not view.export_btn.isEnabled()
    assert not view.copy_btn.isEnabled()


def test_report_view_preview_and_badges(qapp, analyzed_session):
    view = ReportView(session=analyzed_session)
    assert view.export_btn.isEnabled()
    assert view.copy_btn.isEnabled()

    badges = view.section_badges_label.text()
    assert "Design ✓" in badges
    assert "Results ✓" in badges
    assert "Analysis ✓" in badges

    raw_text = view.raw_text_edit.toPlainText()
    assert "# Experiment Report: Report Test Exp" in raw_text
    assert "## Experimental Design" in raw_text
    assert "## Experimental Results" in raw_text
    assert "## Statistical Analysis" in raw_text
    assert "### ANOVA Table" in raw_text


def test_report_view_export(tmp_path, qapp, analyzed_session):
    view = ReportView(session=analyzed_session)
    report_file = str(tmp_path / "final_report.md")

    from doe.report_generation import generate_report
    new_state = generate_report(analyzed_session.workflow_state, output_path=report_file, format="markdown")
    analyzed_session.set_workflow_state(new_state)

    assert os.path.exists(report_file)
    with open(report_file, encoding="utf-8") as f:
        content = f.read()
    assert "# Experiment Report: Report Test Exp" in content
    assert analyzed_session.step == "report_generated"
