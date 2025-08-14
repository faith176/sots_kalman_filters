from abc import ABC, abstractmethod

import numpy as np

from filter.Confidence import compute_confidence

class Filter(ABC):
    @abstractmethod
    def predict(self) -> None:
        """Advance the state estimate one step ahead."""
        pass

    @abstractmethod
    def update(self, measurement) -> None:
        """Update state with a measurement."""
        pass

    @abstractmethod
    def get_value(self) -> float:
        """Get the current estimate of the primary value."""
        pass

    @abstractmethod
    def get_covariance(self):
        """Return the current state covariance matrix."""
        pass

    @abstractmethod
    def get_type(self) -> str:
        """Return filter type/name for identification."""
        pass

    def get_prediction(self) -> tuple[float, float, float]:
        """
        Return a tuple of (estimate, confidence, std_dev) for current state.
        """
        value = self.get_value()
        covariance = self.get_covariance()
        std_dev = np.sqrt(covariance[0, 0])
        confidence = compute_confidence(covariance)
        return value, confidence, std_dev

