"""Placeholder view for upcoming workflow sections."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
)

from doe.gui.styles import (
    get_placeholder_card_style,
    get_placeholder_badge_style,
    colors,
)


class PlaceholderView(QWidget):
    """Clean placeholder view for sections to be implemented incrementally."""

    def __init__(
        self,
        section_title: str,
        description: str,
        upcoming_features: str = "",
        parent: QWidget = None,
    ):
        super().__init__(parent)
        self.section_title = section_title
        self._init_ui(section_title, description, upcoming_features)

    def _init_ui(self, title: str, description: str, upcoming: str) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)

        card = QFrame(self)
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(get_placeholder_card_style())

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)
        card_layout.setAlignment(Qt.AlignCenter)

        # Header badge
        badge = QLabel("UNDER DEVELOPMENT", card)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(get_placeholder_badge_style())
        card_layout.addWidget(badge, alignment=Qt.AlignCenter)

        # Section Title
        title_label = QLabel(title, card)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {colors.HEADER_TEXT};")
        card_layout.addWidget(title_label)

        # Description
        desc_label = QLabel(description, card)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"font-size: 14px; color: {colors.SECONDARY_TEXT}; line-height: 1.4;")
        card_layout.addWidget(desc_label)

        if upcoming:
            note_label = QLabel(upcoming, card)
            note_label.setAlignment(Qt.AlignCenter)
            note_label.setWordWrap(True)
            note_label.setStyleSheet(f"font-size: 12px; color: {colors.SUBTLE_TEXT}; font-style: italic;")
            card_layout.addWidget(note_label)

        layout.addWidget(card, alignment=Qt.AlignCenter)
