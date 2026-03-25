from app.core.source.EventSource import EventSource
import time

class ExperimentEventSource(EventSource):

    def __init__(self, *args, clock=None, scenario=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.clock = clock
        self.scenario = scenario

    def emit_ground_truth(self, params):

        event = self.generate_event(params)

        event["event_status"] = "ground_truth"
        event["partition"] = "ground_truth"

        self.stream.add_event(event, "ground_truth", self.id)

        return event

    def emit_event(self, params):
        return super().emit_event(params)