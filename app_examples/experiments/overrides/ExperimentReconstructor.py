import time

from app.core.compensator.Reconstructor import Reconstructor
from app.core.schema.Event import make_event


class ExperimentalExpectedSchedule:

    def __init__(self, interval, clock=None, grace=0.1):

        self.interval = interval
        self.clock = clock
        self.grace = grace

        now = self.clock.now() if self.clock else time.time()
        self.next_ts = now + interval

    def advance(self):

        self.next_ts += self.interval

    def is_missed(self, now):

        return now > self.next_ts + self.grace


# ----------------------------------------
# NON-THREADED RECONSTRUCTOR
# ----------------------------------------

class ExperimentReconstructor(Reconstructor):

    def __init__(self, *, clock=None, schedule=None, **kwargs):

        # Replace schedule
        if schedule is not None:
            schedule = ExperimentalExpectedSchedule(
                interval=schedule.interval,
                clock=clock,
                grace=schedule.grace if hasattr(schedule, "grace") else 0.1
            )

        super().__init__(schedule=schedule, **kwargs)

        self.clock = clock
        self.last_observed_ts = None
        self._running = False

    # ----------------------------------------

    def start(self):
        # do nothing
        pass

    # ----------------------------------------

    def step(self):
        """
        Manual step: call this from your main loop
        """

        now = self.clock.now() if self.clock else time.time()

        while self.schedule.is_missed(now):

            expected_ts = self.schedule.next_ts

            # Only reconstruct if missing
            if self.last_observed_ts is None or self.last_observed_ts < expected_ts:

                if self.allow_reconstruct:
                    self.reconstruct(expected_ts)

            self.schedule.advance()

    # ----------------------------------------

    def consume_event(self, event):

        ts = event.get(
            "event_ts",
            self.clock.now() if self.clock else time.time()
        )

        self.last_observed_ts = ts

        value = event["value"]

        if self.allow_observe:
            self.predictor.update(value)

        while ts >= self.schedule.next_ts:
            self.schedule.advance()

    # ----------------------------------------

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
                "reconstruction_time": self.clock.now() if self.clock else time.time()
            }
        )