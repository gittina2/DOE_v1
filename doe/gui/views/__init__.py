"""GUI views package."""
from doe.gui.views.experiment_view import ExperimentView
from doe.gui.views.design_view import DesignView
from doe.gui.views.results_view import ResultsView
from doe.gui.views.analysis_view import AnalysisView
from doe.gui.views.report_view import ReportView
from doe.gui.views.placeholder_view import PlaceholderView

__all__ = [
    "ExperimentView",
    "DesignView",
    "ResultsView",
    "AnalysisView",
    "ReportView",
    "PlaceholderView",
]
