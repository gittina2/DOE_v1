"""Session and state management for the DOE Toolkit GUI."""
import os
from typing import Optional
from PySide6.QtCore import QObject, Signal

from doe.models import WorkflowState, WorkflowStep


class GuiSession(QObject):
    """Manages active workflow state, current file path, and dirty tracking."""

    state_changed = Signal(WorkflowState)
    file_path_changed = Signal(str)  # Emits file path or empty string
    dirty_changed = Signal(bool)

    def __init__(self, initial_state: Optional[WorkflowState] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._workflow_state: WorkflowState = initial_state or WorkflowState(step="empty")
        self._current_file_path: Optional[str] = None
        self._is_dirty: bool = False

    @property
    def workflow_state(self) -> WorkflowState:
        return self._workflow_state

    @property
    def current_file_path(self) -> Optional[str]:
        return self._current_file_path

    @property
    def is_dirty(self) -> bool:
        return self._is_dirty

    @property
    def step(self) -> WorkflowStep:
        return self._workflow_state.step

    def set_workflow_state(self, state: WorkflowState, is_dirty: bool = True) -> None:
        """Update active workflow state and notify listeners."""
        self._workflow_state = state
        self._is_dirty = is_dirty
        self.state_changed.emit(self._workflow_state)
        self.dirty_changed.emit(self._is_dirty)

    def set_file_path(self, file_path: Optional[str]) -> None:
        """Update the file path associated with the current workflow."""
        self._current_file_path = file_path
        self.file_path_changed.emit(file_path or "")

    def mark_dirty(self, dirty: bool = True) -> None:
        """Set or clear the dirty (unsaved changes) flag."""
        if self._is_dirty != dirty:
            self._is_dirty = dirty
            self.dirty_changed.emit(self._is_dirty)

    def new_workflow(self) -> None:
        """Reset to a fresh, empty workflow state."""
        self._workflow_state = WorkflowState(step="empty")
        self._current_file_path = None
        self._is_dirty = False
        self.state_changed.emit(self._workflow_state)
        self.file_path_changed.emit("")
        self.dirty_changed.emit(False)

    def load_from_file(self, file_path: str) -> None:
        """Load a workflow state from a JSON file."""
        loaded_state = WorkflowState.load_from_json(file_path)
        self._workflow_state = loaded_state
        self._current_file_path = os.path.abspath(file_path)
        self._is_dirty = False
        self.state_changed.emit(self._workflow_state)
        self.file_path_changed.emit(self._current_file_path)
        self.dirty_changed.emit(False)

    def save_to_file(self, file_path: Optional[str] = None) -> str:
        """Save active workflow state to JSON file."""
        target_path = file_path or self._current_file_path
        if not target_path:
            raise ValueError("No file path provided or associated with current session.")
        abs_path = os.path.abspath(target_path)
        self._workflow_state.validate()
        self._workflow_state.save_to_json(abs_path)
        self._current_file_path = abs_path
        self._is_dirty = False
        self.file_path_changed.emit(abs_path)
        self.dirty_changed.emit(False)
        return abs_path