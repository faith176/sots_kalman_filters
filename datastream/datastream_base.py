from abc import ABC, abstractmethod

class DataStream(ABC):
    @abstractmethod
    def start(self, interval: float):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def get_next_event(self) -> dict:
        pass

    def is_running(self) -> bool:
        return False

    def join(self):
        pass
