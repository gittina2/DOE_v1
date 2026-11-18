"""Unit tests for the AnalysisView GUI component."""
import os
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication, QMessageBox

from doe.gui.session import GuiSession
from doe.gui.views.analysis_view import AnalysisView
from doe.experiment_creation import create_experiment
from doe.design_generation import generate_design
from doe.result_input import insert_results
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
def completed_session():
    session = GuiSession()
    f1 = Factor(name="temp", type="continuous", lower_bound=100.0, upper_bound=200.0)
    f2 = Factor(name="press", type="continuous", lower_bound=1.0, upper_bound=2.0)
    r1 = Response(name="yield", type="continuous")
    r2 = Response(name="purity", type="continuous")
    state = create_experiment(name="Analysis Test Exp", factors=[f1, f2], responses=[r1, r2])
    state = generate_design(state)

    runs = state.design.runs
    entries = [
        ResultEntry(run_ref=runs[0].run_id, values={"yield": 35.5, "purity": 92.1}),
        ResultEntry(run_ref=runs[1].run_id, values={"yield": 40.2, "purity": 94.5}),
        ResultEntry(run_ref=runs[2].run_id, values={"yield": 55.8, "purity": 91.0}),
        ResultEntry(run_ref=runs[3].run_id, values={"yield": 60.1, "purity": 95.2}),
    ]
    state = insert_results(state, entries)
    session.set_workflow_state(state, is_dirty=False)
    return session


def test_analysis_view_eligibility_guardrails(qapp, completed_session):
    view = AnalysisView(session=completed_session)

    # 1. Linear model: 4 observations, 3 parameters (Intercept, temp, press) -> Eligible!
    view.model_type_combo.setCurrentIndex(0)
    is_elig, msg, _, _ = view._check_model_eligibility()
    assert is_elig is True
    assert "Model Estimable" in msg
    assert view.run_btn.isEnabled()

    # 2. Interaction model: 4 observations, 4 parameters (Intercept, temp, press, temp:press) -> N <= p -> Blocked!
    view.model_type_combo.setCurrentIndex(1)
    is_elig, msg, _, _ = view._check_model_eligibility()
    assert is_elig is False
    assert "Insufficient Observations" in msg
    assert not view.run_btn.isEnabled()

    # 3. Quadratic model: 2 levels per factor -> Singular matrix -> Blocked!
    view.model_type_combo.setCurrentIndex(2)
    is_elig, msg, _, _ = view._check_model_eligibility()
    assert is_elig is False
    assert "Non-Estimable Model (Quadratic)" in msg
    assert not view.run_btn.isEnabled()


def test_analysis_view_execution_and_presentation(qapp, completed_session):
    view = AnalysisView(session=completed_session)
    view.model_type_combo.setCurrentIndex(0)  # Linear model
    view.response_combo.setCurrentText("yield")

    view._on_run_analysis()

    assert completed_session.step == "analysis_created"
    assert completed_session.workflow_state.analysis is not None
    assert not view.results_group.isHidden()

    card_text = view.summary_card_label.text()
    assert "yield" in card_text
    assert "R²" in card_text
    assert "Linear Model" in card_text

    assert view.coeffs_table.rowCount() == 3  # Intercept, temp, press
    term_names = [view.coeffs_table.item(r, 0).text() for r in range(view.coeffs_table.rowCount())]
    assert "Intercept" in term_names
    assert "temp" in term_names
    assert "press" in term_names

    assert view.anova_table.rowCount() == 3  # Model, Residuals, Total
    sources = [view.anova_table.item(r, 0).text() for r in range(view.anova_table.rowCount())]
    assert "Model" in sources
    assert "Residuals" in sources
    assert "Total" in sources

    assert view.residuals_table.rowCount() == 4


def test_analysis_view_secondary_response(qapp, completed_session):
    """Verify that user can select and analyze the secondary response."""
    view = AnalysisView(session=completed_session)
    view.model_type_combo.setCurrentIndex(0)
    view.response_combo.setCurrentText("purity")

    view._on_run_analysis()

    assert completed_session.workflow_state.analysis is not None
    assert completed_session.workflow_state.analysis.diagnostics["response_variable"] == "purity"
    assert "purity" in view.summary_card_label.text()
