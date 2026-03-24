import random


class BaseScenario:
    """
    Base class for all experiment scenarios.
    """
    def name(self):
        return self.__class__.__name__

    def get_observation(self, t, value, source_id):
        return value
    

class StableScenario(BaseScenario):
    """
    No disturbance.
    All observations are available and accurate.
    """
    def get_observation(self, t, value, source_id):
        return value
    

class PeriodicDropScenario(BaseScenario):
    def __init__(self, drop_every=5, offset=0):
        self.drop_every = drop_every
        self.offset = offset

    def get_observation(self, t, value, source_id):

        if (t + self.offset) % self.drop_every == 0:
            return None 
        return value


class RandomDropScenario(BaseScenario):

    def __init__(self, drop_prob=0.2, seed=42):
        self.drop_prob = drop_prob
        self.random = random.Random(seed)

    def name(self):
        return f"RandomDrop_p{self.drop_prob}"

    def get_observation(self, t, value, source_id):

        if self.random.random() < self.drop_prob:
            return None

        return value