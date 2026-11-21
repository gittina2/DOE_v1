"""Tests for centralized GUI color management and shared theme styling."""
import os
import re
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from doe.gui.styles import colors
from doe.gui.styles import (
    load_theme_stylesheet,
    get_application_stylesheet,
    get_sidebar_stylesheet,
    get_header_style,
    get_primary_button_style,
    get_success_button_style,
    get_context_frame_style,
    get_calc_frame_style,
    get_status_frame_style,
    get_formula_frame_style,
    get_summary_card_style,
    get_report_overview_frame_style,
    get_badge_style,
    get_eligibility_banner_style,
    get_rendered_browser_style,
    get_raw_editor_style,
    get_placeholder_card_style,
    get_placeholder_badge_style,
)
from doe.gui.app import create_application
from doe.gui.main_window import MainWindow
from doe.gui.session import GuiSession


@pytest.fixture(scope="session")
def qapp():
    """Provides a singleton QApplication instance for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(["-platform", "offscreen"])
    return app


class TestColorDefinitions:
    """Verify integrity of centralized colors.py definitions."""

    def test_hex_colors_valid_format(self):
        """All hex color tokens should follow standard #rrggbb hex notation."""
        hex_regex = re.compile(r"^#[0-9a-fA-F]{6}$")

        tokens = [
            # Base palette
            colors.SLATE_950,
            colors.SLATE_800,
            colors.SLATE_700,
            colors.SLATE_600,
            colors.SLATE_500,
            colors.SLATE_400,
            colors.SLATE_300,
            colors.SLATE_200,
            colors.SLATE_100,
            colors.SLATE_50,
            colors.WHITE,
            colors.BLACK,
            colors.GRAY_800,
            colors.GRAY_700,
            colors.GRAY_600,
            colors.GRAY_500,
            colors.GRAY_400,
            colors.GRAY_300,
            colors.BLUE_800,
            colors.BLUE_700,
            colors.BLUE_600,
            colors.BLUE_200,
            colors.BLUE_50,
            colors.SKY_400,
            colors.BLUE_DARK,
            colors.BLUE_LIGHT,
            colors.GREEN_700,
            colors.GREEN_600,
            colors.GREEN_100,
            colors.AMBER_700,
            colors.AMBER_600,
            colors.AMBER_100,
            colors.RED_600,
            colors.RED_100,
            # Semantic mappings
            colors.HEADER_TEXT,
            colors.BODY_TEXT,
            colors.SECONDARY_TEXT,
            colors.MUTED_TEXT,
            colors.SUBTLE_TEXT,
            colors.HELP_TEXT,
            colors.STATUS_TEXT,
            colors.FORMULA_HDR_TEXT,
            colors.FORMULA_TEXT,
            colors.OVERVIEW_TEXT,
            colors.SIDEBAR_BG,
            colors.SIDEBAR_BORDER,
            colors.SIDEBAR_TITLE,
            colors.SIDEBAR_SUBTITLE,
            colors.SIDEBAR_NAV_TEXT,
            colors.SIDEBAR_NAV_HOVER_BG,
            colors.SIDEBAR_NAV_HOVER_TEXT,
            colors.SIDEBAR_NAV_CHECKED_BG,
            colors.SIDEBAR_NAV_CHECKED_TEXT,
            colors.SIDEBAR_NAV_CHECKED_BORDER,
            colors.SIDEBAR_STATUS_BG,
            colors.SIDEBAR_STATUS_BORDER,
            colors.SIDEBAR_STATUS_HEADING,
            colors.SIDEBAR_STATUS_VALUE,
            colors.PRIMARY_BTN_BG,
            colors.PRIMARY_BTN_HOVER,
            colors.PRIMARY_BTN_PRESSED,
            colors.PRIMARY_BTN_DISABLED_BG,
            colors.PRIMARY_BTN_DISABLED_FG,
            colors.PRIMARY_BTN_TEXT,
            colors.SUCCESS_BTN_BG,
            colors.SUCCESS_BTN_HOVER,
            colors.SUCCESS_BTN_TEXT,
            colors.CARD_BG,
            colors.CARD_BORDER,
            colors.CONTEXT_FRAME_BG,
            colors.CONTEXT_FRAME_BORDER,
            colors.FORMULA_FRAME_BG,
            colors.FORMULA_FRAME_BORDER,
            colors.CALC_FRAME_BG,
            colors.CALC_FRAME_BORDER,
            colors.CALC_FRAME_TEXT,
            colors.PLACEHOLDER_CARD_BG,
            colors.PLACEHOLDER_CARD_BORDER,
            colors.PLACEHOLDER_BADGE_BG,
            colors.PLACEHOLDER_BADGE_TEXT,
            colors.EDITOR_BG,
            colors.EDITOR_FG,
            colors.EDITOR_BORDER,
            colors.BROWSER_BG,
            colors.BROWSER_BORDER,
            colors.BADGE_COMPLETE_BG,
            colors.BADGE_IN_PROGRESS_BG,
            colors.BADGE_PENDING_BG,
            colors.BADGE_INACTIVE_BG,
            colors.BADGE_TEXT,
            colors.ELIGIBLE_BORDER,
            colors.ELIGIBLE_BG,
            colors.WARNING_BORDER,
            colors.WARNING_BG,
            colors.BLOCKED_BORDER,
            colors.BLOCKED_BG,
            colors.ERROR_TEXT,
        ]

        for token in tokens:
            assert isinstance(token, str)
            assert hex_regex.match(token), f"Invalid hex color: {token}"

    def test_qt_colors_valid(self):
        """Table colors must be valid Qt / QColor types."""
        assert colors.TABLE_READONLY_BG in (Qt.lightGray, QColor(Qt.lightGray))
        assert colors.TABLE_STATUS_COMPLETE_FG in (Qt.darkGreen, QColor(Qt.darkGreen))
        assert colors.TABLE_STATUS_PENDING_FG in (Qt.darkRed, QColor(Qt.darkRed))
        assert colors.TABLE_SIG_TERM_BG in (Qt.cyan, QColor(Qt.cyan))
        assert colors.TABLE_SIG_TERM_FG in (Qt.darkGreen, QColor(Qt.darkGreen))
        assert colors.TABLE_NONSIG_TERM_FG in (Qt.darkGray, QColor(Qt.darkGray))
        assert colors.TABLE_WHITE_BG in (Qt.white, QColor(Qt.white))


class TestThemeLoading:
    """Verify theme.qss template processing and substitution."""

    def test_theme_qss_loaded_without_unresolved_tokens(self):
        """load_theme_stylesheet should resolve all @TOKEN@ placeholders."""
        qss = load_theme_stylesheet()
        assert len(qss) > 0
        unresolved = re.findall(r"@[A-Z0-9_]+@", qss)
        assert unresolved == [], f"Found unresolved tokens: {unresolved}"

    def test_theme_contains_key_elements(self):
        """Theme stylesheet must contain sidebar, status box, and component rules."""
        qss = load_theme_stylesheet()
        assert "QWidget#sidebar" in qss
        assert "QPushButton.navButton" in qss
        assert "QFrame#statusFrame" in qss
        assert colors.SIDEBAR_BG in qss
        assert colors.SIDEBAR_BORDER in qss
        assert colors.SKY_400 in qss

    def test_get_application_stylesheet_equals_theme(self):
        """get_application_stylesheet should return the parsed theme stylesheet."""
        assert get_application_stylesheet() == load_theme_stylesheet()

    def test_get_sidebar_stylesheet_contains_sidebar_rules(self):
        """get_sidebar_stylesheet should return stylesheet with sidebar rules."""
        sidebar_qss = get_sidebar_stylesheet()
        assert "QWidget#sidebar" in sidebar_qss
        assert colors.SIDEBAR_BG in sidebar_qss


class TestStyleHelperFunctions:
    """Verify that all component stylesheet generators return correct colors."""

    def test_get_header_style(self):
        style = get_header_style()
        assert f"color: {colors.HEADER_TEXT};" in style
        assert "font-size: 20px;" in style

    def test_get_primary_button_style(self):
        style = get_primary_button_style(font_size="14px", padding="8px 24px", include_disabled=True)
        assert f"background-color: {colors.PRIMARY_BTN_BG};" in style
        assert f"background-color: {colors.PRIMARY_BTN_HOVER};" in style
        assert f"background-color: {colors.PRIMARY_BTN_PRESSED};" in style
        assert f"background-color: {colors.PRIMARY_BTN_DISABLED_BG};" in style
        assert f"color: {colors.PRIMARY_BTN_DISABLED_FG};" in style

    def test_get_success_button_style(self):
        style = get_success_button_style()
        assert f"background-color: {colors.SUCCESS_BTN_BG};" in style
        assert f"background-color: {colors.SUCCESS_BTN_HOVER};" in style

    def test_get_context_frame_style(self):
        style = get_context_frame_style()
        assert f"background-color: {colors.CONTEXT_FRAME_BG};" in style
        assert f"border: 1px solid {colors.CONTEXT_FRAME_BORDER};" in style

    def test_get_calc_frame_style(self):
        style = get_calc_frame_style()
        assert f"background-color: {colors.CALC_FRAME_BG};" in style
        assert f"border: 1px solid {colors.CALC_FRAME_BORDER};" in style

    def test_get_status_frame_style(self):
        style = get_status_frame_style()
        assert f"background-color: {colors.CARD_BG};" in style
        assert f"border: 1px solid {colors.CARD_BORDER};" in style

    def test_get_formula_frame_style(self):
        style = get_formula_frame_style()
        assert f"background-color: {colors.FORMULA_FRAME_BG};" in style
        assert f"border: 1px solid {colors.FORMULA_FRAME_BORDER};" in style

    def test_get_summary_card_style(self):
        style = get_summary_card_style()
        assert f"background-color: {colors.CARD_BG};" in style
        assert f"border: 1px solid {colors.CARD_BORDER};" in style

    def test_get_report_overview_frame_style(self):
        style = get_report_overview_frame_style()
        assert f"background-color: {colors.CARD_BG};" in style
        assert f"border: 1px solid {colors.CARD_BORDER};" in style

    def test_get_badge_style(self):
        style = get_badge_style(colors.BADGE_COMPLETE_BG, bold=True)
        assert f"background-color: {colors.BADGE_COMPLETE_BG};" in style
        assert f"color: {colors.BADGE_TEXT};" in style
        assert "font-weight: bold;" in style

    def test_get_eligibility_banner_style(self):
        style = get_eligibility_banner_style(colors.ELIGIBLE_BG, colors.ELIGIBLE_BORDER)
        assert f"background-color: {colors.ELIGIBLE_BG};" in style
        assert f"border: 1px solid {colors.ELIGIBLE_BORDER};" in style

    def test_get_rendered_browser_style(self):
        style = get_rendered_browser_style()
        assert f"background-color: {colors.BROWSER_BG};" in style
        assert f"border: 1px solid {colors.BROWSER_BORDER};" in style

    def test_get_raw_editor_style(self):
        style = get_raw_editor_style()
        assert f"background-color: {colors.EDITOR_BG};" in style
        assert f"color: {colors.EDITOR_FG};" in style
        assert f"border: 1px solid {colors.EDITOR_BORDER};" in style

    def test_get_placeholder_styles(self):
        card_style = get_placeholder_card_style()
        assert f"background-color: {colors.PLACEHOLDER_CARD_BG};" in card_style
        assert f"border: 1px solid {colors.PLACEHOLDER_CARD_BORDER};" in card_style

        badge_style = get_placeholder_badge_style()
        assert f"background-color: {colors.PLACEHOLDER_BADGE_BG};" in badge_style
        assert f"color: {colors.PLACEHOLDER_BADGE_TEXT};" in badge_style


class TestApplicationStyleIntegration:
    """Verify that styles integrate cleanly into the Qt application and main window."""

    def test_create_application_sets_stylesheet(self, qapp):
        """create_application applies the theme stylesheet."""
        app = create_application([])
        # Verify app has stylesheet set
        assert app.styleSheet() != ""
        assert colors.SIDEBAR_BG in app.styleSheet()

    def test_main_window_sidebar_uses_centralized_style(self, qapp):
        """MainWindow sidebar should have centralized stylesheet applied."""
        session = GuiSession()
        window = MainWindow(session=session)
        sidebar = window.findChild(MainWindow, "sidebar") or window.centralWidget().findChild(type(window.centralWidget()), "sidebar")
        # Direct check on sidebar widget
        sidebar_widget = None
        for child in window.centralWidget().children():
            if hasattr(child, "objectName") and child.objectName() == "sidebar":
                sidebar_widget = child
                break

        assert sidebar_widget is not None
        assert colors.SIDEBAR_BG in sidebar_widget.styleSheet()
        assert colors.SIDEBAR_BORDER in sidebar_widget.styleSheet()
