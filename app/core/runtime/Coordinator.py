import logging
import threading
import time
from typing import Dict
from dataclasses import dataclass, field

from ..schema.Event import Event
from ..reconstruction.Reconstructor import Reconstructor
from ..utils.UtilsFuncs import _load_json
from ..runtime.EventConsumer import EventConsumer

from app.state_charts.lvls.lv4 import Statechart

__author__ = "Feyi Adesanya"


# ---------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------

class ExpectedSchedule:
    def __init__(
        self,
        interval: float,
        start_ts: float | None = None,
        grace: float = 0.1,
    ):
        now = time.time()
        self.interval = interval
        self.next_ts = start_ts or (now + interval)
        self.grace = grace

    def advance(self):
        self.next_ts += self.interval

    def is_missed(self, now: float) -> bool:
        return now > self.next_ts + self.grace


# ---------------------------------------------------------------------
# Constituent Context (NEW)
# ---------------------------------------------------------------------

@dataclass
class ConstituentContext:
    source_id: str
    schedule: ExpectedSchedule
    reconstructor: Reconstructor
    state_machine: Statechart
    last_event_ts: float = field(default_factory=time.time)


# ---------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------

class Coordinator(EventConsumer):
    """
    Consumes observed events via EventStream callbacks,
    tracks expected schedules per source,
    triggers reconstruction on absence,
    and manages SoTS lifecycle state machines.
    """

    def __init__(
        self,
        *,
        event_stream,
        sources_config_path: str,
        predictors_config_path: str,
        check_interval: float = 0.05,
    ):
        self.event_stream = event_stream
        self.sources_cfg = _load_json(sources_config_path)
        self.predictors_cfg = _load_json(predictors_config_path)

        # NEW unified registry
        self.constituents: Dict[str, ConstituentContext] = {}

        self._running = False
        self._thread: threading.Thread | None = None
        self.check_interval = check_interval

        self._setup()

    # -----------------------------------------------------------------

    def _setup(self):

        for source_id, cfg in self.sources_cfg.items():

            interval = cfg.get("interval", 1.0)
            grace = cfg.get("grace", 0.1)

            schedule = ExpectedSchedule(
                interval=interval,
                grace=grace,
            )

            predictor = self._build_predictor(cfg["predictor_template"])

            reconstructor = Reconstructor(
                source_id=source_id,
                predictor=predictor,
                event_stream=self.event_stream,
            )

            # -------------------------
            # State machine
            # -------------------------

            sm = Statechart()
            sm.enter()

            # Initialize lifecycle
            sm.raise_prepare_for_so_s()
            sm.raise_join_so_s()

            context = ConstituentContext(
                source_id=source_id,
                schedule=schedule,
                reconstructor=reconstructor,
                state_machine=sm,
            )

            self.constituents[source_id] = context

            self.event_stream.subscribe(
                consumer=self,
                partition="observed",
                source_id=source_id,
            )

            logging.info(f"[COORDINATOR] Subscribed to observed.{source_id}")

    # -----------------------------------------------------------------

    def _build_predictor(self, template_name: str):

        from ..reconstruction.PredictorRegistry import get_predictor_class

        cfg = self.predictors_cfg[template_name]
        cls = get_predictor_class(cfg["type"])
        return cls(**cfg.get("params", {}))

    # -----------------------------------------------------------------

    def consume_event(self, event: Event) -> None:
        """
        Observed event advances the expected schedule
        and updates Kalman reconstruction + reliability state.
        """

        try:
            source_id = event["src"]
            ts = event.get("event_ts", time.time())
        except Exception:
            logging.warning("[COORDINATOR] Malformed event received")
            return

        ctx = self.constituents.get(source_id)

        if not ctx:
            return

        schedule = ctx.schedule
        reconstructor = ctx.reconstructor
        sm = ctx.state_machine

        ctx.last_event_ts = ts

        # Advance schedule
        while ts >= schedule.next_ts:
            schedule.advance()

        # --------------------------------
        # Kalman update
        # --------------------------------

        result = reconstructor.handle_observed(event)

        # --------------------------------
        # Health transitions
        # --------------------------------

        # if residual is not None:

        #     if residual > 50:
        #         sm.raise_component_deviation()

        # # Recovery
        # if residual is not None and residual <= 50:
        #     sm.raise_recovery()

        # --------------------------------
        # Participation transitions
        # --------------------------------

        if sm.belong_id == sm.PASSIVE_ID:
            sm.raise_join_constellation()

        logging.debug(
            f"[COORDINATOR] Observed event from {source_id} at {ts:.3f}, "
            f"next expected at {schedule.next_ts:.3f}"
        )

    # -----------------------------------------------------------------

    def _monitor_loop(self):

        self._running = True

        logging.info("[COORDINATOR] monitor started")

        while self._running:

            now = time.time()

            for ctx in self.constituents.values():

                schedule = ctx.schedule
                reconstructor = ctx.reconstructor
                sm = ctx.state_machine
                source_id = ctx.source_id

                if schedule.is_missed(now):

                    expected_ts = schedule.next_ts

                    logging.debug(
                        f"[COORDINATOR] Missing event from {source_id} "
                        f"(expected at {expected_ts:.3f})"
                    )

                    # -------------------------
                    # State machine disturbance
                    # -------------------------

                    sm.raise_leave_request()

                    # -------------------------
                    # Reconstruction
                    # -------------------------

                    reconstructor.reconstruct(expected_ts)

                    schedule.advance()

            if not self.constituents:
                time.sleep(0.1)
                continue

            # Sleep until next deadline
            now = time.time()

            next_deadline = min(
                ctx.schedule.next_ts + ctx.schedule.grace
                for ctx in self.constituents.values()
            )

            sleep_for = max(0.0, next_deadline - now)
            sleep_for = min(sleep_for, 0.5)

            time.sleep(sleep_for)

        logging.info("[COORDINATOR] monitor stopped")

    # -----------------------------------------------------------------
    # Lifecycle
    # -----------------------------------------------------------------

    def start(self):

        if self._running:
            return

        self._thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="coordinator-monitor",
        )

        self._thread.start()

    # -----------------------------------------------------------------

    def stop(self):

        self._running = False

        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

        logging.info("[COORDINATOR] Shutting down...")

    # -----------------------------------------------------------------
    # Debug Helper
    # -----------------------------------------------------------------

    def get_constituent_state(self, source_id):

        ctx = self.constituents.get(source_id)

        if not ctx:
            return None

        sm = ctx.state_machine

        return {
            "belong_id": sm.belong_id,
            "health_id": sm.health_id,
        }