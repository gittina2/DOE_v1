"""Main application window for DOE Toolkit."""
import os
from typing import Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QKeySequence, QCloseEvent
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QPushButton,
    QButtonGroup,
    QLabel,
    QFileDialog,
    QMessageBox,
    QToolBar,
    QStatusBar,
    QFrame,
)

from doe.gui.session import GuiSession
from doe.gui.views.experiment_view import ExperimentView
from doe.gui.views.placeholder_view import PlaceholderView
from doe.models import (
    SchemaVersionMismatchError,
    WorkflowStateMismatchError,
    DomainValidationError,
    DoeError,
)


class MainWindow(QMainWindow):
    """Main window with persistent sidebar and central workflow views."""

    SECTION_NAMES = ["Experiment", "Design", "Results", "Analysis", "Report"]

    def __init__(self, session: Optional[GuiSession] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.session = session or GuiSession(parent=self)

        self.setWindowTitle("DOE Toolkit")
        self.resize(1100, 720)
        self.setMinimumSize(850, 550)

        self._init_actions()
        self._init_menu()
        self._init_toolbar()
        self._init_ui()
        self._init_statusbar()
        self._connect_signals()

        self._update_window_title()
        self._update_workflow_status()

    def _init_actions(self) -> None:
        self.action_new = QAction("&New", self)
        self.action_new.setShortcut(QKeySequence.New)
        self.action_new.setStatusTip("Start a new workflow")
        self.action_new.triggered.connect(self.on_new_workflow)

        self.action_open = QAction("&Open Workflow...", self)
        self.action_open.setShortcut(QKeySequence.Open)
        self.action_open.setStatusTip("Load an existing workflow JSON file")
        self.action_open.triggered.connect(self.on_open_workflow)

        self.action_save = QAction("&Save", self)
        self.action_save.setShortcut(QKeySequence.Save)
        self.action_save.setStatusTip("Save the active workflow")
        self.action_save.triggered.connect(self.on_save_workflow)

        self.action_save_as = QAction("Save &As...", self)
        self.action_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.action_save_as.setStatusTip("Save the active workflow to a new file")
        self.action_save_as.triggered.connect(self.on_save_as_workflow)

        self.action_exit = QAction("E&xit", self)
        self.action_exit.setShortcut(QKeySequence.Quit)
        self.action_exit.setStatusTip("Exit the application")
        self.action_exit.triggered.connect(self.close)

    def _init_menu(self) -> None:
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.action_new)
        file_menu.addAction(self.action_open)
        file_menu.addSeparator()
        file_menu.addAction(self.action_save)
        file_menu.addAction(self.action_save_as)
        file_menu.addSeparator()
        file_menu.addAction(self.action_exit)

    def _init_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        toolbar.addAction(self.action_new)
        toolbar.addAction(self.action_open)
        toolbar.addAction(self.action_save)
        toolbar.addAction(self.action_save_as)
        self.addToolBar(toolbar)

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Persistent Left Sidebar
        sidebar = self._create_sidebar()
        root_layout.addWidget(sidebar)

        # Central Content Area
        self.stack = QStackedWidget(self)
        self._create_views()
        root_layout.addWidget(self.stack, 1)

    def _create_sidebar(self) -> QWidget:
        sidebar = QWidget(self)
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        sidebar.setStyleSheet(
            """
            QWidget#sidebar {
                background-color: #1e293b;
                border-right: 1px solid #334155;
            }
            QLabel#appTitle {
                color: #ffffff;
                font-size: 18px;
                font-weight: bold;
                padding: 16px 12px 6px 12px;
            }
            QLabel#appSubtitle {
                color: #94a3b8;
                font-size: 11px;
                padding: 0 12px 16px 12px;
            }
            QPushButton.navButton {
                background-color: transparent;
                color: #cbd5e1;
                font-size: 14px;
                text-align: left;
                padding: 12px 18px;
                border: none;
                border-left: 4px solid transparent;
                font-weight: 500;
            }
            QPushButton.navButton:hover {
                background-color: #334155;
                color: #ffffff;
            }
            QPushButton.navButton:checked {
                background-color: #334155;
                color: #38bdf8;
                border-left: 4px solid #38bdf8;
                font-weight: bold;
            }
            QFrame#statusFrame {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                margin: 10px;
                padding: 10px;
            }
            QLabel#statusHeading {
                color: #94a3b8;
                font-size: 11px;
                text-transform: uppercase;
                font-weight: bold;
            }
            QLabel#statusValue {
                color: #38bdf8;
                font-size: 13px;
                font-weight: bold;
            }
            """
        )

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # App branding header
        title_label = QLabel("DOE Toolkit", sidebar)
        title_label.setObjectName("appTitle")
        layout.addWidget(title_label)

        sub_label = QLabel("Design of Experiments", sidebar)
        sub_label.setObjectName("appSubtitle")
        layout.addWidget(sub_label)

        # Navigation button group
        self.nav_button_group = QButtonGroup(sidebar)
        self.nav_button_group.setExclusive(True)
        self.nav_buttons = []

        for idx, name in enumerate(self.SECTION_NAMES):
            btn = QPushButton(f"  {name}", sidebar)
            btn.setProperty("class", "navButton")
            btn.setCheckable(True)
            if idx == 0:
                btn.setChecked(True)
            self.nav_button_group.addButton(btn, idx)
            layout.addWidget(btn)
            self.nav_buttons.append(btn)

        self.nav_button_group.idClicked.connect(self._on_nav_clicked)

        layout.addStretch(1)

        # Workflow Status indicator at the bottom of sidebar
        status_frame = QFrame(sidebar)
        status_frame.setObjectName("statusFrame")
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(8, 8, 8, 8)
        status_layout.setSpacing(4)

        heading_label = QLabel("Workflow State", status_frame)
        heading_label.setObjectName("statusHeading")
        status_layout.addWidget(heading_label)

        self.status_value_label = QLabel("Empty", status_frame)
        self.status_value_label.setObjectName("statusValue")
        self.status_value_label.setWordWrap(True)
        status_layout.addWidget(self.status_value_label)

        layout.addWidget(status_frame)

        return sidebar

    def _create_views(self) -> None:
        # Index 0: Experiment View
        self.experiment_view = ExperimentView(self.session, self)
        self.stack.addWidget(self.experiment_view)

        # Index 1: Design View
        design_view = PlaceholderView(
            section_title="Design",
            description="Experimental design generation (Full Factorial, Fractional Factorial) will be configured and generated here.",
            upcoming_features="Step 2 of the DOE workflow: build design matrices, view coded levels, and randomize runs.",
            parent=self,
        )
        self.stack.addWidget(design_view)

        # Index 2: Results View
        results_view = PlaceholderView(
            section_title="Results",
            description="Experimental response data entry, inspection, and CSV result importing will be managed here.",
            upcoming_features="Step 3 of the DOE workflow: record measurement values and validate completeness.",
            parent=self,
        )
        self.stack.addWidget(results_view)

        # Index 3: Analysis View
        analysis_view = PlaceholderView(
            section_title="Analysis",
            description="Statistical regression modeling (Linear, Interaction, Quadratic) and ANOVA computations will be displayed here.",
            upcoming_features="Step 4 of the DOE workflow: evaluate coefficients, p-values, R², and model diagnostics.",
            parent=self,
        )
        self.stack.addWidget(analysis_view)

        # Index 4: Report View
        report_view = PlaceholderView(
            section_title="Report",
            description="Structured Markdown report generation, viewing, and export will be handled here.",
            upcoming_features="Step 5 of the DOE workflow: export publication-ready reports summarizing the complete experimental pipeline.",
            parent=self,
        )
        self.stack.addWidget(report_view)

    def _init_statusbar(self) -> None:
        statusbar = QStatusBar(self)
        self.setStatusBar(statusbar)
        self.statusBar().showMessage("Ready")

    def _connect_signals(self) -> None:
        self.session.state_changed.connect(self._on_session_state_changed)
        self.session.file_path_changed.connect(self._on_session_file_path_changed)
        self.session.dirty_changed.connect(self._on_session_dirty_changed)

    def _on_nav_clicked(self, index: int) -> None:
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)

    def _on_session_state_changed(self) -> None:
        self._update_workflow_status()

    def _on_session_file_path_changed(self) -> None:
        self._update_window_title()

    def _on_session_dirty_changed(self) -> None:
        self._update_window_title()

    def _update_window_title(self) -> None:
        file_path = self.session.current_file_path
        if file_path:
            name = os.path.basename(file_path)
        else:
            name = "Untitled"

        dirty_marker = " *" if self.session.is_dirty else ""
        self.setWindowTitle(f"DOE Toolkit - [{name}]{dirty_marker}")

    def _update_workflow_status(self) -> None:
        step = self.session.step
        formatted = step.replace("_", " ").title()
        self.status_value_label.setText(formatted)

    def _prompt_save_changes_if_dirty(self) -> bool:
        """Returns True if it is safe to proceed, False if user cancelled."""
        if not self.session.is_dirty:
            return True

        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes in the current workflow.\nDo you want to save them before continuing?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save,
        )

        if reply == QMessageBox.Save:
            return self.on_save_workflow()
        elif reply == QMessageBox.Discard:
            return True
        else:
            return False

    def on_new_workflow(self) -> bool:
        if not self._prompt_save_changes_if_dirty():
            return False
        self.session.new_workflow()
        self.nav_buttons[0].setChecked(True)
        self.stack.setCurrentIndex(0)
        self.statusBar().showMessage("Started new empty workflow.", 3000)
        return True

    def on_open_workflow(self) -> bool:
        if not self._prompt_save_changes_if_dirty():
            return False

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Workflow JSON",
            "",
            "JSON Files (*.json);;All Files (*)",
        )
        if not file_path:
            return False

        try:
            self.session.load_from_file(file_path)
            self.statusBar().showMessage(f"Loaded workflow: {os.path.basename(file_path)}", 4000)
            return True
        except SchemaVersionMismatchError as e:
            QMessageBox.critical(
                self,
                "Unsupported Schema Version",
                f"Failed to load workflow file:\n\n{str(e)}",
            )
        except (WorkflowStateMismatchError, DomainValidationError) as e:
            QMessageBox.critical(
                self,
                "Workflow Validation Error",
                f"The workflow file contains invalid data:\n\n{str(e)}",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "File Load Error",
                f"An error occurred while opening the workflow file:\n\n{str(e)}",
            )
        return False

    def on_save_workflow(self) -> bool:
        if not self.session.current_file_path:
            return self.on_save_as_workflow()

        try:
            saved_path = self.session.save_to_file()
            self.statusBar().showMessage(f"Saved: {os.path.basename(saved_path)}", 4000)
            return True
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Could not save workflow file:\n\n{str(e)}",
            )
            return False

    def on_save_as_workflow(self) -> bool:
        suggested = self.session.current_file_path or "workflow.json"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Workflow As",
            suggested,
            "JSON Files (*.json);;All Files (*)",
        )
        if not file_path:
            return False

        try:
            saved_path = self.session.save_to_file(file_path)
            self.statusBar().showMessage(f"Saved: {os.path.basename(saved_path)}", 4000)
            return True
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save As Error",
                f"Could not save workflow file:\n\n{str(e)}",
            )
            return False

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._prompt_save_changes_if_dirty():
            event.accept()
        else:
            event.ignore()
