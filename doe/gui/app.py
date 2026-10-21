"""Application entry point and Qt application lifecycle."""
import sys
from typing import Optional, List

from PySide6.QtWidgets import QApplication

from doe.gui.main_window import MainWindow
from doe.gui.session import GuiSession


def create_application(argv: Optional[List[str]] = None) -> QApplication:
    """Create or return the existing QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(argv if argv is not None else sys.argv)
        app.setApplicationName("DOE Toolkit")
        app.setOrganizationName("DOE Toolkit")
    return app


def run_app(argv: Optional[List[str]] = None) -> int:
    """Run the PySide6 desktop GUI."""
    app = create_application(argv)
    session = GuiSession()
    window = MainWindow(session=session)
    window.show()
    return app.exec()
