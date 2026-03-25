import random

class BaseScenario:
    def name(self):
        return self.__class__.__name__

    def get_observation(self, t, value, source_id):
        return value

    def get_health(self, t, current_health, source_id):
        return current_health
    
    def get_belonging(self, t, current_belonging, source_id):
        return current_belonging
    
class StableScenario(BaseScenario):
    def get_observation(self, t, value, source_id):
        return value

    def get_health(self, t, current_health, source_id):
        return "ideal"
    


class ProgressiveDegradationScenario(BaseScenario):
    def __init__(self, seed=42):
        self.random = random.Random(seed)

        self.health_schedule = [
            (0, "ideal"),
            (10, "defective"),
            (20, "faulty"),
            (30, "erroneous"),
            (40, "malfunctioning"),
            (55, "erroneous"),
            (70, "faulty"),
            (85, "defective"),
            (100, "ideal"),
        ]

        self.drop_map = {
            "ideal": 0.0,
            "defective": 0.025,
            "faulty": 0.05,
            "erroneous": 0.25,
            "malfunctioning": 0.35,
        }

    def name(self):
        return "ProgressiveDegradation"

    def get_health(self, t, current_health, source_id):

        health = "ideal"

        for ts, h in self.health_schedule:
            if t >= ts:
                health = h

        return health

    def get_observation(self, t, value, source_id):
        health = self.get_health(t, None, source_id)
        drop_prob = self.drop_map.get(health, 0.0)

        if self.random.random() < drop_prob:
            return None

        return value



    
# class PeriodicDropScenario(BaseScenario):
#     def __init__(self, drop_every=5, offset=0):
#         self.drop_every = drop_every
#         self.offset = offset

#     def get_observation(self, t, value, source_id):
#         if (t + self.offset) % self.drop_every == 0:
#             return None 
#         return value
    
# class RandomDropScenario(BaseScenario):

#     def __init__(self, drop_prob=0.2, seed=42):
#         self.drop_prob = drop_prob
#         self.random = random.Random(seed)

#     def name(self):
#         return f"RandomDrop_p{self.drop_prob}"

#     def get_observation(self, t, value, source_id):
#         if self.random.random() < self.drop_prob:
#             return None
#         return value