from abc import ABC, abstractmethod

class DataStream(ABC):
    def __init__(self, sensor_id, name):
        self.sensor_id = sensor_id
        self.name = name

    @abstractmethod
    def start(self, interval: float):
        pass

    @abstractmethod
    def stop(self):
        pass

    def is_running(self) -> bool:
        return False

    def join(self):
        pass

    def get_name(self):
        return self.name
