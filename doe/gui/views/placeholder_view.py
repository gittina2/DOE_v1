"""Placeholder view for upcoming workflow sections."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFrame,
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
        card.setStyleSheet(
            """
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 30px;
                max-width: 600px;
            }
            """
        )

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)
        card_layout.setAlignment(Qt.AlignCenter)

        # Header badge
        badge = QLabel("UNDER DEVELOPMENT", card)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            """
            background-color: #e3f2fd;
            color: #0d47a1;
            font-size: 11px;
            font-weight: bold;
            padding: 4px 12px;
            border-radius: 4px;
            """
        )
        card_layout.addWidget(badge, alignment=Qt.AlignCenter)

        # Section Title
        title_label = QLabel(title, card)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #1a1a1a;")
        card_layout.addWidget(title_label)

        # Description
        desc_label = QLabel(description, card)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 14px; color: #555555; line-height: 1.4;")
        card_layout.addWidget(desc_label)

        if upcoming:
            note_label = QLabel(upcoming, card)
            note_label.setAlignment(Qt.AlignCenter)
            note_label.setWordWrap(True)
            note_label.setStyleSheet("font-size: 12px; color: #777777; font-style: italic;")
            card_layout.addWidget(note_label)

        layout.addWidget(card, alignment=Qt.AlignCenter)
