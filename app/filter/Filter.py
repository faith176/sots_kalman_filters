from abc import ABC, abstractmethod

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

