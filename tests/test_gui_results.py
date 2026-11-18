"""Unit tests for the ResultsView GUI component."""
import os
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication, QMessageBox

from doe.gui.session import GuiSession
from doe.gui.views.results_view import ResultsView
from doe.experiment_creation import create_experiment
from doe.design_generation import generate_design
from doe.result_input import export_results_template_csv
from doe.models import Factor, Response


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
def designed_session():
    session = GuiSession()
    f1 = Factor(name="temp", type="continuous", lower_bound=100.0, upper_bound=200.0)
    r1 = Response(name="yield", type="continuous")
    state = create_experiment(name="Results Test Exp", factors=[f1], responses=[r1])
    state = generate_design(state)
    session.set_workflow_state(state, is_dirty=False)
    return session


def test_results_view_without_design(qapp):
    session = GuiSession()
    view = ResultsView(session=session)
    assert not view.export_template_btn.isEnabled()
    assert not view.import_csv_btn.isEnabled()
    assert not view.save_btn.isEnabled()


def test_results_view_template_export(tmp_path, qapp, designed_session):
    view = ResultsView(session=designed_session)
    template_path = str(tmp_path / "template.csv")

    export_results_template_csv(
        designed_session.workflow_state.design,
        designed_session.workflow_state.experiment,
        template_path,
    )
    assert os.path.exists(template_path)
    with open(template_path, encoding="utf-8") as f:
        content = f.read()
    assert "run_number,run_id,temp,yield" in content


def test_results_view_manual_entry_and_save(qapp, designed_session):
    view = ResultsView(session=designed_session)
    assert view.results_table.rowCount() == 2  # 1 factor -> 2 runs

    # Enter partial results (only row 0)
    # Col 0: Run #, 1: Run ID, 2: temp, 3: yield, 4: Status
    view.results_table.item(0, 3).setText("45.5")
    view._on_save_results()

    assert designed_session.step == "results_in_progress"
    assert "In Progress" in view.status_badge.text()

    # Enter remaining result (row 1)
    view.results_table.item(1, 3).setText("78.2")
    view._on_save_results()

    assert designed_session.step == "results_complete"
    assert "Complete" in view.status_badge.text()


def test_results_view_csv_import(tmp_path, qapp, designed_session):
    view = ResultsView(session=designed_session)
    runs = designed_session.workflow_state.design.runs

    csv_path = tmp_path / "measured_results.csv"
    csv_content = f"run_id,yield\n{runs[0].run_id},50.5\n{runs[1].run_id},80.2\n"
    csv_path.write_text(csv_content, encoding="utf-8")

    from doe.imports.csv_result_importer import import_results_from_csv
    from doe.result_input import insert_results

    entries = import_results_from_csv(
        str(csv_path),
        design=designed_session.workflow_state.design,
        responses=designed_session.workflow_state.experiment.responses,
    )
    new_state = insert_results(designed_session.workflow_state, entries)
    designed_session.set_workflow_state(new_state)

    assert designed_session.step == "results_complete"
    assert len(designed_session.workflow_state.results.entries) == 2


def test_results_view_clear(qapp, designed_session):
    view = ResultsView(session=designed_session)
    view.results_table.item(0, 3).setText("45.5")
    view.results_table.item(1, 3).setText("78.2")
    view._on_save_results()
    assert designed_session.step == "results_complete"

    view._on_clear_results()
    assert designed_session.step == "design_generated"
    assert designed_session.workflow_state.results is None
