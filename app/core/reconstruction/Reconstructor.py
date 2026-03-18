import threading
import time
import logging

from ..schema.EventConsumer import EventConsumer
from ..schema.EventGenerator import EventGenerator
from ..schema.Event import make_event
from .predictor_types import *


class Reconstructor(EventConsumer, EventGenerator):

    """
    Reconstructor service responsible for compensating missing
    events using a predictor (e.g., Kalman filter).

    Behaviour:

    passive / full_role  → update predictor with observations
    restricted_role      → reconstruct missing events
    """

    # --------------------------------
    # POLICY CONFIGURATION
    # --------------------------------

    CONSUME_POLICY = {
        "passive": "observe",
        "pending_exit": "observe",
        "pending_entry": "observe",
        "full_role": "observe",
    }

    MONITOR_POLICY = {
        "restricted_role": "reconstruct",
    }

    # --------------------------------

    def __init__(
        self,
        *,
        source_id,
        predictor,
        event_stream,
        lifecycle,
        schedule
    ):

        self.source_id = source_id
        self.predictor = predictor
        self.stream = event_stream
        self.lifecycle = lifecycle
        self.schedule = schedule

        self._running = False

        # Subscribe to all observed partitions
        self.stream.subscribe(self, "observed.*", self.source_id)

    # --------------------------------
    # EVENT GENERATION
    # --------------------------------

    def generate_event(self, event_params):

        return make_event(
            type="simulated",
            src=self.source_id,
            event_status="reconstructed",
            value=event_params["prediction"],
            event_ts=event_params["expected_ts"],
            confidence=event_params["confidence"],
            extras={
                "interval": self.schedule.interval,
                "reconstruction_method": getattr(self.predictor, "name", "predictor"),
                "reconstruction_time": time.time()
            }
        )

    # --------------------------------

    def emit_event(self, event_params):

        event = self.generate_event(event_params)

        # attach partition metadata for logging
        event["partition"] = "reconstructed"


        ctx = self.lifecycle.constituents.get(self.source_id)
        if ctx:
            ctx.reconstructed_events += 1

        self.stream.add_event(
            event,
            "reconstructed",
            self.source_id
        )

        return event

    # --------------------------------
    # EVENT CONSUMPTION
    # --------------------------------

    def consume_event(self, event):

        ts = event.get("event_ts", time.time())

        state = self.lifecycle.get_state(self.source_id)

        if not state:
            return

        belonging_main = state["belonging_main"]
        belonging_sub = state["belonging_sub"]

        policy = (
            self.CONSUME_POLICY.get(belonging_sub)
            or self.CONSUME_POLICY.get(belonging_main)
        )

        value = event["value"]

        logging.debug(
            f"[RECONSTRUCTOR-{self.source_id}] "
            f"state={belonging_main}/{belonging_sub} "
            f"value={value}"
        )

        if policy == "observe":
            self.predictor.update(value)

        while ts >= self.schedule.next_ts:
            self.schedule.advance()



    def start(self):

        if self._running:
            return

        self._running = True

        threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name=f"reconstructor-{self.source_id}"
        ).start()

    # --------------------------------

    def _monitor_loop(self):

        while self._running:
            while self.schedule.is_missed(time.time()):

                state = self.lifecycle.get_state(self.source_id)

                if state:

                    belonging_sub = state["belonging_sub"]

                    logging.debug(
                        f"[RECONSTRUCTOR-{self.source_id}] "
                        f"missed event | state={belonging_sub}"
                    )

                    policy = self.MONITOR_POLICY.get(belonging_sub)

                    if policy == "reconstruct":

                        self.reconstruct(self.schedule.next_ts)

                self.schedule.advance()

            time.sleep(0.05)

    # --------------------------------
    # RECONSTRUCTION
    # --------------------------------

    def reconstruct(self, expected_ts):

        prediction = self.predictor.predict()
        confidence = self.predictor.confidence()

        self.emit_event({
            "prediction": prediction,
            "expected_ts": expected_ts,
            "confidence": confidence
        })

        logging.info(
            f"[RECONSTRUCTION] {self.source_id} "
            f"prediction={prediction:.3f} "
            f"confidence={confidence:.3f}"
            f"reconstructed event at {expected_ts}"
        )