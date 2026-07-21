"""Abstract interface for DOE design generators.

Workflow orchestration code depends only on this interface,
never on a concrete algorithm implementation.
"""

from abc import ABC, abstractmethod

from doe.models.experiment import Experiment
from doe.models.design import Design


class DesignGenerator(ABC):
    """Base class that every design generator must implement.

    A generator receives a **validated** Experiment and returns a
    **validated** Design.  Concrete subclasses supply the algorithm
    (e.g. full‑factorial, fractional‑factorial, …).
    """

    @abstractmethod
    def generate(self, experiment: Experiment) -> Design:
        """Generate a Design from the given Experiment.

        Parameters
        ----------
        experiment : Experiment
            A fully validated Experiment instance.

        Returns
        -------
        Design
            A validated Design containing all generated runs.

        Raises
        ------
        DoeError (or subclass)
            If the experiment cannot be used to produce a valid design.
        """
        ...
