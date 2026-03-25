import logging
import random

from app.core.source.EventSourceRegistry import register_source_type
from app_examples.experiments.overrides.ExperimentEventSource import ExperimentEventSource


@register_source_type("simulated_experiment")
class SimulatedEventSource(ExperimentEventSource):

    def __init__(
        self,
        *,
        id,
        type,
        stream,
        lifecycle,
        value_unit=None,
        value_datatype="scalar",
        interval=1.0,
        min_value=0.0,
        max_value=100.0,
        drift=0.2,
        noise=0.5,
        start_value=None,
    ):
        super().__init__(id=id, type=type, stream=stream, lifecycle=lifecycle)

        self.interval = interval
        self.min_value = min_value
        self.max_value = max_value
        self.drift = drift
        self.noise = noise

        self.value_unit = value_unit
        self.value_datatype = value_datatype

        self.current_value = (
            start_value if start_value is not None
            else random.uniform(min_value, max_value)
        )

        self.scenario = None
        self.clock = None


    def override_observation(self, scenario, clock):
        self.scenario = scenario
        self.clock = clock


    def step(self, now):
        drift = random.uniform(-self.drift, self.drift)
        noise = random.gauss(0, self.noise)

        self.current_value += drift + noise

        self.current_value = max(
            self.min_value,
            min(self.current_value, self.max_value)
        )

        true_value = self.current_value

        self.emit_ground_truth({
            "value": true_value,
            "event_ts": now,
            "value_unit": self.value_unit,
            "confidence": 1.0,
            "value_datatype": self.value_datatype,
            "extras": {
                "drift": drift,
                "noise": noise,
                "type": "ground_truth"
            }
        })

        if now % self.interval != 0:
            return None

        observed_value = true_value

        if self.scenario:
            observed_value = self.scenario.get_observation(
                now, true_value, self.id
            )

        if observed_value is None:
            logging.debug(f"[SOURCE {self.id}] DROPPED at t={now}")
            return None

        logging.debug(f"[SOURCE {self.id}] Observed emit at t={now}")

        return self.emit_event({
            "value": observed_value,
            "event_ts": now,
            "confidence": 1.0,
            "value_unit": self.value_unit,
            "value_datatype": self.value_datatype,
            "extras": {
                "drift": drift,
                "noise": noise
            }
        })