import logging
import time
from typing import Dict
from dataclasses import dataclass, field


class ExperimentClock:

    start_time = time.time()

    @staticmethod
    def now():
        return time.time() - ExperimentClock.start_time


@dataclass
class ConstituentContext:

    source_id: str
    runtime: object
    event_source: object
    reconstructor: object
    schedule: object

    last_event_ts: float = field(default_factory=time.time)

    observed_events: int = 0
    reconstructed_events: int = 0


class LifecycleManager:

    def __init__(self):
        self.constituents: Dict[str, ConstituentContext] = {}

    # --------------------------------------------------
    # REGISTRATION
    # --------------------------------------------------

    def register_constituent(
        self,
        source_id,
        runtime,
        event_source,
        reconstructor,
        schedule
    ):

        ctx = ConstituentContext(
            source_id=source_id,
            runtime=runtime,
            event_source=event_source,
            reconstructor=reconstructor,
            schedule=schedule
        )

        self.constituents[source_id] = ctx

        logging.info(f"[LIFECYCLE] Registered {source_id}")

    # --------------------------------------------------
    # STATE ACCESS
    # --------------------------------------------------

    def get_state(self, source_id):

        ctx = self.constituents.get(source_id)

        if not ctx:
            return None

        return ctx.runtime.state_snapshot()

    def get_runtime(self, source_id):

        ctx = self.constituents.get(source_id)

        if not ctx:
            return None

        return ctx.runtime

    # --------------------------------------------------
    # EVENT METRICS
    # --------------------------------------------------

    def increment_observed(self, source_id):

        ctx = self.constituents.get(source_id)

        if ctx:
            ctx.observed_events += 1
            ctx.last_event_ts = ExperimentClock.now()

    def increment_reconstructed(self, source_id):

        ctx = self.constituents.get(source_id)

        if ctx:
            ctx.reconstructed_events += 1

    # --------------------------------------------------
    # METRICS EXPORT
    # --------------------------------------------------

    def metrics(self):

        results = {}

        for source_id, ctx in self.constituents.items():

            results[source_id] = {
                "observed": ctx.observed_events,
                "reconstructed": ctx.reconstructed_events,
                "last_event_time": ctx.last_event_ts
            }

        return results

    def system_event_totals(self):

        observed = 0
        reconstructed = 0

        for ctx in self.constituents.values():

            observed += ctx.observed_events
            reconstructed += ctx.reconstructed_events

        return {
            "observed": observed,
            "reconstructed": reconstructed,
            "total": observed + reconstructed
        }

    # --------------------------------------------------
    # SYSTEM SNAPSHOT
    # --------------------------------------------------

    def snapshot(self):

        stats = {
            "full_role": 0,
            "restricted_role": 0,
            "passive": 0,
            "degraded": 0,
            "failed": 0,
        }

        for ctx in self.constituents.values():

            state = ctx.runtime.state_snapshot()

            role = state["belonging_sub"]
            health = state["health_main"]

            if role == "restricted_role":
                stats["restricted_role"] += 1

            elif role == "full_role":
                stats["full_role"] += 1

            elif state["belonging_main"] == "passive":
                stats["passive"] += 1

            if health == "degraded":
                stats["degraded"] += 1

            if health == "failed":
                stats["failed"] += 1

        return stats

    # --------------------------------------------------
    # GLOBAL LIFECYCLE CONTROL
    # --------------------------------------------------

    def activate_all(self):

        logging.info("[LIFECYCLE] Activating all constituents")

        for source_id, ctx in self.constituents.items():

            runtime = ctx.runtime

            try:
                runtime.ensure_active()

            except Exception as e:

                logging.warning(
                    f"[LIFECYCLE] Failed to activate {source_id}: {e}"
                )

    # --------------------------------------------------
    # DEBUG
    # --------------------------------------------------

    def print_states(self):

        for source_id, ctx in self.constituents.items():

            state = ctx.runtime.state_snapshot()

            logging.info(
                f"{source_id} | "
                f"{state['belonging_main']} / {state['belonging_sub']} | "
                f"{state['health_main']}"
            )