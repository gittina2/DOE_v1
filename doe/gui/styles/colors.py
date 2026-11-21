"""Centralized color palette and semantic color tokens for DOE Toolkit GUI.

This module is the single source of truth for all colors used across the application.
Colors are organized into:
1. Base Palette: Raw hex constants (Slate, Blue, Green, Amber, Red, Gray).
2. Semantic Colors: Named tokens mapped to specific UI roles (headers, buttons, cards, statuses).
3. Qt/Table Colors: QColor / Qt.GlobalColor definitions for QTableWidget cells and table items.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

# =============================================================================
# 1. Base Color Palette
# =============================================================================

# Slate Neutrals
SLATE_950 = "#0f172a"
SLATE_900 = "#0f172a"
SLATE_800 = "#1e293b"
SLATE_700 = "#334155"
SLATE_600 = "#475569"
SLATE_500 = "#64748b"
SLATE_400 = "#94a3b8"
SLATE_300 = "#cbd5e1"
SLATE_200 = "#e2e8f0"
SLATE_100 = "#f1f5f9"
SLATE_50 = "#f8fafc"

# Monochromes
WHITE = "#ffffff"
BLACK = "#000000"

# Grays
GRAY_800 = "#1a1a1a"
GRAY_700 = "#333333"
GRAY_600 = "#555555"
GRAY_500 = "#666666"
GRAY_400 = "#777777"
GRAY_300 = "#e0e0e0"

# Blues / Accents
BLUE_800 = "#1e40af"
BLUE_700 = "#1d4ed8"
BLUE_600 = "#2563eb"
BLUE_200 = "#bfdbfe"
BLUE_50 = "#eff6ff"
SKY_400 = "#38bdf8"
BLUE_DARK = "#0d47a1"
BLUE_LIGHT = "#e3f2fd"

# Greens (Success)
GREEN_700 = "#15803d"
GREEN_600 = "#16a34a"
GREEN_100 = "#dcfce7"

# Ambers (Warning)
AMBER_700 = "#b45309"
AMBER_600 = "#d97706"
AMBER_100 = "#fef3c7"

# Reds (Danger / Error)
RED_600 = "#dc2626"
RED_100 = "#fee2e2"


# =============================================================================
# 2. Semantic Color Mappings
# =============================================================================

# Typography / Text Colors
HEADER_TEXT = WHITE          # "#1a1a1a" (main view headers)
BODY_TEXT = WHITE            # "#333333" (body / summary text)
SECONDARY_TEXT = GRAY_600       # "#555555" (placeholder description)
MUTED_TEXT = GRAY_500           # "#666666" (response dialog type label)
SUBTLE_TEXT = GRAY_400          # "#777777" (placeholder notes)
HELP_TEXT = SLATE_500           # "#64748b" (table helper hints, report italic preview)
STATUS_TEXT = SLATE_700         # "#334155" (results status label)
FORMULA_HDR_TEXT = SLATE_600    # "#475569" (analysis formula header)
FORMULA_TEXT = SLATE_950        # "#0f172a" (analysis formula display)
OVERVIEW_TEXT = SLATE_800       # "#1e293b" (report overview label)

# Sidebar
SIDEBAR_BG = SLATE_800                  # "#1e293b"
SIDEBAR_BORDER = SLATE_700              # "#334155"
SIDEBAR_TITLE = WHITE                   # "#ffffff"
SIDEBAR_SUBTITLE = SLATE_400            # "#94a3b8"
SIDEBAR_NAV_TEXT = SLATE_300            # "#cbd5e1"
SIDEBAR_NAV_HOVER_BG = SLATE_700        # "#334155"
SIDEBAR_NAV_HOVER_TEXT = WHITE          # "#ffffff"
SIDEBAR_NAV_CHECKED_BG = SLATE_700       # "#334155"
SIDEBAR_NAV_CHECKED_TEXT = SKY_400      # "#38bdf8"
SIDEBAR_NAV_CHECKED_BORDER = SKY_400    # "#38bdf8"
SIDEBAR_STATUS_BG = SLATE_950           # "#0f172a"
SIDEBAR_STATUS_BORDER = SLATE_700       # "#334155"
SIDEBAR_STATUS_HEADING = SLATE_400      # "#94a3b8"
SIDEBAR_STATUS_VALUE = SKY_400          # "#38bdf8"

# Buttons
PRIMARY_BTN_BG = BLUE_600               # "#2563eb"
PRIMARY_BTN_HOVER = BLUE_700            # "#1d4ed8"
PRIMARY_BTN_PRESSED = BLUE_800          # "#1e40af"
PRIMARY_BTN_DISABLED_BG = SLATE_400     # "#94a3b8"
PRIMARY_BTN_DISABLED_FG = SLATE_200     # "#e2e8f0"
PRIMARY_BTN_TEXT = WHITE                # "#ffffff"

SUCCESS_BTN_BG = GREEN_600              # "#16a34a"
SUCCESS_BTN_HOVER = GREEN_700           # "#15803d"
SUCCESS_BTN_TEXT = WHITE                # "#ffffff"

# Frames, Cards & Containers
CARD_BG = SLATE_50                      # "#f8fafc"
CARD_BORDER = SLATE_300                 # "#cbd5e1"
CONTEXT_FRAME_BG = SLATE_100            # "#f1f5f9"
CONTEXT_FRAME_BORDER = SLATE_300        # "#cbd5e1"
FORMULA_FRAME_BG = SLATE_50             # "#f8fafc"
FORMULA_FRAME_BORDER = SLATE_200        # "#e2e8f0"
CALC_FRAME_BG = BLUE_50                 # "#eff6ff"
CALC_FRAME_BORDER = BLUE_200            # "#bfdbfe"
CALC_FRAME_TEXT = BLUE_800              # "#1e40af"

# Placeholder Specific
PLACEHOLDER_CARD_BG = WHITE             # "#ffffff"
PLACEHOLDER_CARD_BORDER = GRAY_300      # "#e0e0e0"
PLACEHOLDER_BADGE_BG = BLUE_LIGHT       # "#e3f2fd"
PLACEHOLDER_BADGE_TEXT = BLUE_DARK      # "#0d47a1"

# Raw Code / Syntax Editor
EDITOR_BG = SLATE_950                   # "#0f172a"
EDITOR_FG = SLATE_50                    # "#f8fafc"
EDITOR_BORDER = SLATE_700               # "#334155"

# Rendered Browser
BROWSER_BG = WHITE                      # "#ffffff"
BROWSER_BORDER = SLATE_300              # "#cbd5e1"

# Badges & Feedback Banners
BADGE_COMPLETE_BG = GREEN_600           # "#16a34a"
BADGE_IN_PROGRESS_BG = AMBER_600        # "#d97706"
BADGE_PENDING_BG = SLATE_500            # "#64748b"
BADGE_INACTIVE_BG = SLATE_400           # "#94a3b8"
BADGE_TEXT = WHITE                      # "#ffffff"

ELIGIBLE_BORDER = GREEN_600             # "#16a34a"
ELIGIBLE_BG = GREEN_100                 # "#dcfce7"
WARNING_BORDER = AMBER_700              # "#b45309"
WARNING_BG = AMBER_100                  # "#fef3c7"
BLOCKED_BORDER = RED_600                # "#dc2626"
BLOCKED_BG = RED_100                    # "#fee2e2"
ERROR_TEXT = RED_600                    # "#dc2626"


# =============================================================================
# 3. Table Cell Palette (Qt / QColor definitions)
# =============================================================================

TABLE_READONLY_BG = Qt.lightGray
TABLE_STATUS_COMPLETE_FG = Qt.darkGreen
TABLE_STATUS_PENDING_FG = Qt.darkRed
TABLE_SIG_TERM_BG = Qt.cyan
TABLE_SIG_TERM_FG = Qt.darkGreen
TABLE_NONSIG_TERM_FG = Qt.darkGray
TABLE_WHITE_BG = Qt.white
