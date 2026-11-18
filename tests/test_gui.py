"""Unit and integration tests for the PySide6 DOE Toolkit GUI foundation."""
import os
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication, QMessageBox

from doe.gui.session import GuiSession
from doe.gui.main_window import MainWindow
from doe.gui.dialogs.factor_dialog import FactorDialog
from doe.gui.dialogs.response_dialog import ResponseDialog
from doe.models import Factor, Response, WorkflowState


@pytest.fixture(scope="session")
def qapp():
    """Provides a singleton QApplication instance for GUI tests."""
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
def session():
    """Provides a clean GuiSession for each test."""
    return GuiSession()


@pytest.fixture
def main_window(qapp, session):
    """Provides an instantiated MainWindow."""
    window = MainWindow(session=session)
    return window


def test_main_window_initialization(main_window):
    """Verify window title, dimensions, sidebar, and initial state."""
    assert "DOE Toolkit" in main_window.windowTitle()
    assert main_window.stack.count() == 5
    assert main_window.session.step == "empty"
    assert main_window.status_value_label.text() == "Empty"


def test_sidebar_navigation_switching(main_window):
    """Verify navigation buttons switch stacked widget views."""
    for idx in range(5):
        main_window.nav_buttons[idx].click()
        assert main_window.stack.currentIndex() == idx


def test_factor_dialog_continuous(qapp):
    """Verify FactorDialog for continuous factors."""
    dialog = FactorDialog()
    dialog.name_edit.setText("Temperature")
    dialog.type_combo.setCurrentIndex(0)  # Continuous
    dialog.lower_bound_edit.setText("50.0")
    dialog.upper_bound_edit.setText("150.0")
    dialog.unit_edit.setText("°C")
    dialog._on_accept()

    factor = dialog.get_factor()
    assert factor is not None
    assert factor.name == "Temperature"
    assert factor.type == "continuous"
    assert factor.lower_bound == 50.0
    assert factor.upper_bound == 150.0
    assert factor.unit == "°C"


def test_factor_dialog_categorical(qapp):
    """Verify FactorDialog for categorical factors."""
    dialog = FactorDialog()
    dialog.name_edit.setText("Catalyst")
    dialog.type_combo.setCurrentIndex(1)  # Categorical
    dialog.level_input.setText("CatA")
    dialog._add_level()
    dialog.level_input.setText("CatB")
    dialog._add_level()
    dialog._on_accept()

    factor = dialog.get_factor()
    assert factor is not None
    assert factor.name == "Catalyst"
    assert factor.type == "categorical"
    assert factor.levels == ["CatA", "CatB"]


def test_response_dialog(qapp):
    """Verify ResponseDialog creation."""
    dialog = ResponseDialog()
    dialog.name_edit.setText("Yield")
    dialog.unit_edit.setText("%")
    dialog._on_accept()

    response = dialog.get_response()
    assert response is not None
    assert response.name == "Yield"
    assert response.type == "continuous"
    assert response.unit == "%"


def test_experiment_creation_in_gui(main_window):
    """Verify defining and creating an experiment through ExperimentView."""
    view = main_window.experiment_view
    view.name_edit.setText("GUI Test Experiment")
    view.description_edit.setPlainText("Test description")

    f1 = Factor(name="temp", type="continuous", lower_bound=100.0, upper_bound=200.0)
    f2 = Factor(name="press", type="continuous", lower_bound=1.0, upper_bound=2.0)
    r1 = Response(name="yield", type="continuous", unit="%")

    view._factors = [f1, f2]
    view._responses = [r1]

    created = view._on_create_experiment()
    assert created is True
    assert main_window.session.step == "experiment_created"
    assert main_window.session.is_dirty is True
    assert main_window.session.workflow_state.experiment.name == "GUI Test Experiment"


def test_session_save_and_load(tmp_path, session):
    """Verify saving and loading workflow JSON via GuiSession."""
    f1 = Factor(name="temp", type="continuous", lower_bound=100.0, upper_bound=200.0)
    r1 = Response(name="yield", type="continuous")
    from doe.experiment_creation import create_experiment
    state = create_experiment(name="Saved Exp", factors=[f1], responses=[r1])

    session.set_workflow_state(state, is_dirty=True)
    json_file = str(tmp_path / "test_session_workflow.json")

    saved_path = session.save_to_file(json_file)
    assert os.path.exists(saved_path)
    assert session.is_dirty is False
    assert session.current_file_path == os.path.abspath(json_file)

    # Load in new session
    new_session = GuiSession()
    new_session.load_from_file(json_file)
    assert new_session.step == "experiment_created"
    assert new_session.workflow_state.experiment.name == "Saved Exp"
    assert new_session.is_dirty is False
