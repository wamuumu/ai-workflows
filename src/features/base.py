from abc import ABC, abstractmethod

class FeatureBase(ABC):
    """Abstract base class for enhancement features."""

    _phase: str

    @abstractmethod
    def apply(self, context, debug: bool):
        """Apply the enhancement feature, modifying the initial prompt or the final workflow."""
        pass

    def get_phase(self) -> str:
        """Get the phase of the enhancement feature."""
        return self._phase