"""Shared Qt styling mechanism and helper functions for DOE Toolkit GUI."""
from pathlib import Path
import re
from typing import Optional

from doe.gui.styles import colors

THEME_QSS_PATH = Path(__file__).parent / "theme.qss"


def load_theme_stylesheet() -> str:
    """Load theme.qss and replace all @TOKEN@ tokens with colors from colors.py."""
    if not THEME_QSS_PATH.exists():
        return ""
    qss = THEME_QSS_PATH.read_text(encoding="utf-8")

    def _replacer(match: re.Match) -> str:
        token = match.group(1)
        if hasattr(colors, token):
            return str(getattr(colors, token))
        return match.group(0)

    return re.sub(r"@([A-Z0-9_]+)@", _replacer, qss)


def get_application_stylesheet() -> str:
    """Return the global application stylesheet generated from theme.qss."""
    return load_theme_stylesheet()


def get_sidebar_stylesheet() -> str:
    """Return the stylesheet specifically for the sidebar widget."""
    return load_theme_stylesheet()


def get_header_style() -> str:
    """Return common section header style."""
    return f"font-size: 20px; font-weight: bold; color: {colors.HEADER_TEXT};"


def get_primary_button_style(
    font_size: str = "14px",
    padding: str = "10px 24px",
    border_radius: str = "6px",
    include_disabled: bool = False,
    border_none: bool = True,
) -> str:
    """Return stylesheet for primary action buttons."""
    border_prop = "border: none;\n" if border_none else ""
    disabled_css = ""
    if include_disabled:
        disabled_css = f"""
            QPushButton:disabled {{
                background-color: {colors.PRIMARY_BTN_DISABLED_BG};
                color: {colors.PRIMARY_BTN_DISABLED_FG};
            }}"""

    return f"""
            QPushButton {{
                background-color: {colors.PRIMARY_BTN_BG};
                color: {colors.PRIMARY_BTN_TEXT};
                font-size: {font_size};
                font-weight: bold;
                padding: {padding};
                border-radius: {border_radius};
                {border_prop}
            }}
            QPushButton:hover {{
                background-color: {colors.PRIMARY_BTN_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {colors.PRIMARY_BTN_PRESSED};
            }}{disabled_css}
    """.strip()


def get_success_button_style(
    padding: str = "6px 16px",
    border_radius: str = "4px",
) -> str:
    """Return stylesheet for success action buttons."""
    return f"""
            QPushButton {{
                background-color: {colors.SUCCESS_BTN_BG};
                color: {colors.SUCCESS_BTN_TEXT};
                font-weight: bold;
                padding: {padding};
                border-radius: {border_radius};
            }}
            QPushButton:hover {{
                background-color: {colors.SUCCESS_BTN_HOVER};
            }}
    """.strip()


def get_context_frame_style() -> str:
    """Return stylesheet for design context frame."""
    return f"""
            QFrame#contextFrame {{
                background-color: {colors.CONTEXT_FRAME_BG};
                border: 1px solid {colors.CONTEXT_FRAME_BORDER};
                border-radius: 6px;
                padding: 12px;
            }}
    """.strip()


def get_calc_frame_style() -> str:
    """Return stylesheet for run calculator frame."""
    return f"""
            QFrame#calcFrame {{
                background-color: {colors.CALC_FRAME_BG};
                border: 1px solid {colors.CALC_FRAME_BORDER};
                border-radius: 6px;
                padding: 8px 12px;
            }}
    """.strip()


def get_status_frame_style() -> str:
    """Return stylesheet for status and overview frames."""
    return f"""
            QFrame#statusFrame {{
                background-color: {colors.CARD_BG};
                border: 1px solid {colors.CARD_BORDER};
                border-radius: 6px;
                padding: 10px 14px;
            }}
    """.strip()


def get_formula_frame_style() -> str:
    """Return stylesheet for analysis formula preview frame."""
    return f"""
            QFrame#formulaFrame {{
                background-color: {colors.FORMULA_FRAME_BG};
                border: 1px solid {colors.FORMULA_FRAME_BORDER};
                border-radius: 6px;
                padding: 10px 14px;
            }}
    """.strip()


def get_summary_card_style() -> str:
    """Return stylesheet for analysis summary card."""
    return f"""
            QFrame#summaryCard {{
                background-color: {colors.CARD_BG};
                border: 1px solid {colors.CARD_BORDER};
                border-radius: 6px;
                padding: 12px;
            }}
    """.strip()


def get_report_overview_frame_style() -> str:
    """Return stylesheet for report overview container."""
    return f"""
            QFrame#reportOverviewFrame {{
                background-color: {colors.CARD_BG};
                border: 1px solid {colors.CARD_BORDER};
                border-radius: 6px;
                padding: 10px 14px;
            }}
    """.strip()


def get_badge_style(
    bg_color: str,
    color: str = colors.BADGE_TEXT,
    bold: bool = False,
    border_radius: str = "4px",
    padding: str = "4px 10px",
) -> str:
    """Return stylesheet for a status badge label."""
    weight = "font-weight: bold; " if bold else ""
    return f"background-color: {bg_color}; color: {color}; {weight}border-radius: {border_radius}; padding: {padding};"


def get_eligibility_banner_style(bg_color: str, border_color: str) -> str:
    """Return stylesheet for model eligibility banner frame."""
    return f"QFrame {{ background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 6px; padding: 6px; }}"


def get_rendered_browser_style(
    padding: str = "16px",
    border_radius: str = "4px",
) -> str:
    """Return stylesheet for rendered HTML report browser."""
    return f"""
            QTextBrowser {{
                background-color: {colors.BROWSER_BG};
                border: 1px solid {colors.BROWSER_BORDER};
                border-radius: {border_radius};
                padding: {padding};
                font-size: 13px;
                line-height: 1.5;
            }}
    """.strip()


def get_raw_editor_style(
    padding: str = "12px",
    border_radius: str = "4px",
) -> str:
    """Return stylesheet for raw markdown editor."""
    return f"""
            QTextEdit, QPlainTextEdit {{
                font-family: Consolas, monospace;
                font-size: 12px;
                background-color: {colors.EDITOR_BG};
                color: {colors.EDITOR_FG};
                padding: {padding};
                border: 1px solid {colors.EDITOR_BORDER};
                border-radius: {border_radius};
            }}
    """.strip()


def get_placeholder_card_style() -> str:
    """Return stylesheet for placeholder card."""
    return f"""
            QFrame {{
                background-color: {colors.PLACEHOLDER_CARD_BG};
                border: 1px solid {colors.PLACEHOLDER_CARD_BORDER};
                border-radius: 8px;
                padding: 30px;
                max-width: 600px;
            }}
    """.strip()


def get_placeholder_badge_style() -> str:
    """Return stylesheet for placeholder badge."""
    return f"""
            background-color: {colors.PLACEHOLDER_BADGE_BG};
            color: {colors.PLACEHOLDER_BADGE_TEXT};
            font-size: 11px;
            font-weight: bold;
            padding: 4px 12px;
            border-radius: 4px;
    """.strip()
