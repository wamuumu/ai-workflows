from abc import ABC, abstractmethod
from typing import Literal

class FeatureBase(ABC):
    """Abstract base class for enhancement features."""

    _phase: Literal["pre", "post"]

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @abstractmethod
    def apply(self, context, max_retries: int, debug: bool):
        """Apply the enhancement feature, modifying the initial prompt or the final workflow."""
        pass

    def get_phase(self) -> str:
        """Get the phase of the enhancement feature."""
        return self._phase