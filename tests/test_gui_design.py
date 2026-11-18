"""Unit tests for the DesignView GUI component."""
import os
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication, QMessageBox

from doe.gui.session import GuiSession
from doe.gui.views.design_view import DesignView
from doe.experiment_creation import create_experiment
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
def populated_session():
    session = GuiSession()
    f1 = Factor(name="temp", type="continuous", lower_bound=100.0, upper_bound=200.0)
    f2 = Factor(name="press", type="continuous", lower_bound=1.0, upper_bound=2.0)
    r1 = Response(name="yield", type="continuous")
    state = create_experiment(name="Design Test Exp", factors=[f1, f2], responses=[r1])
    session.set_workflow_state(state, is_dirty=False)
    return session


def test_design_view_without_experiment(qapp):
    session = GuiSession()
    view = DesignView(session=session)
    assert not view.config_group.isEnabled()
    assert not view.generate_btn.isEnabled()
    assert not view.inspection_group.isVisible()


def test_design_view_run_count_calculation(qapp, populated_session):
    view = DesignView(session=populated_session)
    assert view.config_group.isEnabled()
    assert view.generate_btn.isEnabled()

    # Full factorial for 2 continuous factors: 2^2 = 4 runs
    view.design_type_combo.setCurrentIndex(0)
    assert "4" in view.run_calc_label.text()

    # Fractional factorial for 2 factors falls back to 4
    view.design_type_combo.setCurrentIndex(1)
    assert "4" in view.run_calc_label.text()


def test_design_view_generate_and_inspect(qapp, populated_session):
    view = DesignView(session=populated_session)
    view._on_generate_design()

    assert populated_session.step == "design_generated"
    assert populated_session.workflow_state.design is not None
    assert len(populated_session.workflow_state.design.runs) == 4
    assert not view.inspection_group.isHidden()

    # Check run table
    assert view.run_table.rowCount() == 4
    assert view.run_table.columnCount() == 4  # Run #, Run ID, temp, press

    # Check coded table
    assert view.coded_table.rowCount() == 4
    val_0 = view.coded_table.item(0, 2).text()
    assert "-1.0" in val_0 or "+1.0" in val_0


def test_design_view_export_csv_and_excel(tmp_path, qapp, populated_session):
    view = DesignView(session=populated_session)
    view._on_generate_design()

    csv_path = str(tmp_path / "exported_design.csv")
    from doe.designs.utils import export_design_to_csv, export_design_to_excel
    export_design_to_csv(populated_session.workflow_state.design, populated_session.workflow_state.experiment, csv_path)

    assert os.path.exists(csv_path)
    with open(csv_path, encoding="utf-8") as f:
        content = f.read()
    assert "Run Number,Run ID,temp,press" in content
    assert "100.0" in content

    excel_path = str(tmp_path / "exported_design.xml")
    export_design_to_excel(populated_session.workflow_state.design, populated_session.workflow_state.experiment, excel_path)
    assert os.path.exists(excel_path)
    with open(excel_path, encoding="utf-8") as f:
        xml_content = f.read()
    assert "Workbook" in xml_content or "Run Number" in xml_content
