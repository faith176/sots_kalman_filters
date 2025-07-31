from abc import ABC, abstractmethod

class Filter(ABC):
    @abstractmethod
    def predict(self):
        pass

    @abstractmethod
    def update(self, measurement):
        pass

    @abstractmethod
    def get_value(self):
        pass

    @abstractmethod
    def get_covariance(self):
        pass

    @abstractmethod
    def get_type(self):
        pass

