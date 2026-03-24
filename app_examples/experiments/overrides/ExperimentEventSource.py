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

        now = self.clock.now() if self.clock else params.get("event_ts", time.time())

        ground_truth_value = params["value"]

        self.emit_ground_truth({
            **params,
            "value": ground_truth_value,
            "event_ts": now,
            "extras": {
                **(params.get("extras") or {}),
                "type": "ground_truth"
            }
        })

        observed_value = ground_truth_value

        if self.scenario:
            observed_value = self.scenario.get_observation(
                t=now,
                value=ground_truth_value,
                source_id=self.id
            )

        if observed_value is None:
            return None

        observed_params = {
            **params,
            "value": observed_value,
            "event_ts": now,
        }

        return super().emit_event(observed_params)