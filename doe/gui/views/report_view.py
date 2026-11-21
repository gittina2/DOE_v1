"""Functional Report view for live Markdown report previewing, syntax inspection, and publication export."""
import os
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QGroupBox,
    QMessageBox,
    QScrollArea,
    QFrame,
    QTabWidget,
    QFileDialog,
)

from doe.gui.session import GuiSession
from doe.report_generation import format_markdown_report, generate_report
from doe.models import DoeError, DomainValidationError
from doe.gui.styles import (
    get_header_style,
    get_status_frame_style,
    get_primary_button_style,
    get_rendered_browser_style,
    get_raw_editor_style,
    colors,
)


class ReportView(QWidget):
    """In-window Markdown report previewer, raw source inspector, and export view."""

    report_exported = Signal(str)

    def __init__(self, session: GuiSession, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.session = session
        self._current_report_text = ""

        self._init_ui()
        self._connect_signals()
        self._refresh_view()

    def _init_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(24, 20, 24, 20)
        self._content_layout.setSpacing(16)

        # -- Section Header --
        header = QLabel("Experiment Report & Export", content)
        header.setStyleSheet(get_header_style())
        self._content_layout.addWidget(header)

        # -- Overview & Status Banner --
        self.overview_frame = QFrame(content)
        self.overview_frame.setObjectName("reportOverviewFrame")
        self.overview_frame.setStyleSheet(get_status_frame_style())
        overview_layout = QHBoxLayout(self.overview_frame)
        overview_layout.setContentsMargins(8, 8, 8, 8)

        self.overview_label = QLabel(self.overview_frame)
        self.overview_label.setTextFormat(Qt.RichText)
        self.overview_label.setStyleSheet(f"font-size: 13px; color: {colors.OVERVIEW_TEXT};")
        overview_layout.addWidget(self.overview_label, 1)

        self.section_badges_label = QLabel(self.overview_frame)
        self.section_badges_label.setTextFormat(Qt.RichText)
        overview_layout.addWidget(self.section_badges_label)

        self._content_layout.addWidget(self.overview_frame)

        # -- Export Toolbar --
        toolbar_group = QGroupBox("Report Actions & Export", content)
        toolbar_layout = QHBoxLayout(toolbar_group)

        fmt_label = QLabel("Format:", toolbar_group)
        fmt_label.setStyleSheet("font-weight: bold;")
        toolbar_layout.addWidget(fmt_label)

        self.format_combo = QComboBox(toolbar_group)
        self.format_combo.addItem("Markdown (.md)", "markdown")
        self.format_combo.setToolTip("Markdown is the publication-ready report format supported by the core engine.")
        toolbar_layout.addWidget(self.format_combo)

        self.export_btn = QPushButton("Export Report to File...", toolbar_group)
        self.export_btn.setStyleSheet(get_primary_button_style(padding="6px 18px", border_radius="4px", border_none=False))
        self.export_btn.clicked.connect(self._on_export_report)
        toolbar_layout.addWidget(self.export_btn)

        self.copy_btn = QPushButton("Copy to Clipboard", toolbar_group)
        self.copy_btn.clicked.connect(self._on_copy_to_clipboard)
        toolbar_layout.addWidget(self.copy_btn)

        self.refresh_btn = QPushButton("Refresh Preview", toolbar_group)
        self.refresh_btn.clicked.connect(self._refresh_view)
        toolbar_layout.addWidget(self.refresh_btn)

        toolbar_layout.addStretch(1)
        self._content_layout.addWidget(toolbar_group)

        # -- Preview Container (Tabbed: Rendered vs Raw) --
        self.preview_group = QGroupBox("Report Inspection", content)
        preview_layout = QVBoxLayout(self.preview_group)

        self.tabs = QTabWidget(self.preview_group)

        # Tab 1: Rendered Markdown Browser
        self.rendered_browser = QTextBrowser(self.tabs)
        self.rendered_browser.setObjectName("renderedReportBrowser")
        self.rendered_browser.setOpenExternalLinks(True)
        self.rendered_browser.setMinimumHeight(450)
        self.rendered_browser.setStyleSheet(get_rendered_browser_style(padding="16px", border_radius="4px"))
        self.tabs.addTab(self.rendered_browser, "Formatted Document Preview")

        # Tab 2: Raw Markdown Source
        self.raw_text_edit = QTextEdit(self.tabs)
        self.raw_text_edit.setObjectName("rawReportEditor")
        self.raw_text_edit.setReadOnly(True)
        self.raw_text_edit.setMinimumHeight(450)
        self.raw_text_edit.setStyleSheet(get_raw_editor_style(padding="12px", border_radius="4px"))
        self.tabs.addTab(self.raw_text_edit, "Raw Markdown Syntax")

        preview_layout.addWidget(self.tabs)
        self._content_layout.addWidget(self.preview_group)
        self._content_layout.addStretch(1)

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

    def _connect_signals(self) -> None:
        self.session.state_changed.connect(self._on_session_state_changed)

    # ------------------------------------------------------------------ #
    #  View Synchronization                                               #
    # ------------------------------------------------------------------ #

    def _on_session_state_changed(self) -> None:
        self._refresh_view()

    def _refresh_view(self) -> None:
        state = self.session.workflow_state
        exp = state.experiment if state else None

        if exp is None:
            self.overview_label.setText("<b>No Experiment Defined:</b> Please create an experiment first.")
            self.section_badges_label.setText("")
            self.export_btn.setEnabled(False)
            self.copy_btn.setEnabled(False)
            self.rendered_browser.setHtml(
                f"<p style='color: {colors.HELP_TEXT}; font-style: italic;'>"
                "Report preview will be generated automatically once an experiment is created."
                "</p>"
            )
            self.raw_text_edit.clear()
            self._current_report_text = ""
            return

        self.export_btn.setEnabled(True)
        self.copy_btn.setEnabled(True)

        # Overview banner
        step_title = state.step.replace("_", " ").title()
        self.overview_label.setText(
            f"<b>Active Experiment:</b> {exp.name} &nbsp;|&nbsp; <b>Current Step:</b> {step_title}"
        )

        # Section Badges
        has_des = state.design is not None
        has_res = state.results is not None and bool(state.results.entries)
        has_ana = state.analysis is not None

        def _badge(title: str, present: bool) -> str:
            color = colors.BADGE_COMPLETE_BG if present else colors.BADGE_INACTIVE_BG
            icon = "✓" if present else "–"
            return f"<span style='background-color: {color}; color: {colors.BADGE_TEXT}; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-left: 4px;'>{title} {icon}</span>"

        badges_html = (
            _badge("Design", has_des)
            + _badge("Results", has_res)
            + _badge("Analysis", has_ana)
        )
        self.section_badges_label.setText(f"<b>Included Sections:</b> {badges_html}")

        # Generate markdown report
        try:
            self._current_report_text = format_markdown_report(state)
            self.rendered_browser.setMarkdown(self._current_report_text)
            self.raw_text_edit.setPlainText(self._current_report_text)
        except Exception as e:
            self.rendered_browser.setHtml(f"<p style='color: {colors.ERROR_TEXT};'>Error rendering report: {str(e)}</p>")
            self.raw_text_edit.setPlainText(f"Error: {str(e)}")

    # ------------------------------------------------------------------ #
    #  Actions                                                            #
    # ------------------------------------------------------------------ #

    def _on_export_report(self) -> None:
        state = self.session.workflow_state
        if not state.experiment:
            QMessageBox.warning(self, "No Experiment", "Cannot export a report without an experiment.")
            return

        suggested = f"{state.experiment.name.replace(' ', '_')}_report.md"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Experiment Report",
            suggested,
            "Markdown Files (*.md);;All Files (*)",
        )
        if not file_path:
            return

        try:
            new_state = generate_report(state, output_path=file_path, format="markdown")
            self.session.set_workflow_state(new_state, is_dirty=True)
            self.report_exported.emit(file_path)
            QMessageBox.information(
                self,
                "Report Exported",
                f"Report successfully generated and saved to:\n{os.path.basename(file_path)}",
            )
        except (DoeError, DomainValidationError) as e:
            QMessageBox.critical(self, "Export Error", f"Failed to generate report:\n\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "System Error", f"An unexpected error occurred:\n\n{str(e)}")

    def _on_copy_to_clipboard(self) -> None:
        if not self._current_report_text:
            return
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self._current_report_text)
        QMessageBox.information(self, "Copied", "Report Markdown copied to system clipboard.")

