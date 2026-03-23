import logging
import time
from typing import Dict
from dataclasses import dataclass, field

from ..utils.EventListener.Logger import LifecycleLogger

# ==================================================
# CONTEXT
# ==================================================

@dataclass
class ConstituentContext:

    source_id: str
    runtime: object
    event_source: object
    reconstructor: object
    schedule: object

    last_event_ts: float = field(default_factory=time.time)


# ==================================================
# LIFECYCLE MANAGER
# ==================================================

class LifecycleManager:

    def __init__(self, run_dir: str):
        self.constituents: Dict[str, ConstituentContext] = {}
        self.lifecycle_logger = LifecycleLogger(run_dir)

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
                runtime.ensure_participating()

            except Exception as e:

                logging.warning(
                    f"[LIFECYCLE] Failed to activate {source_id}: {e}"
                )

    # --------------------------------------------------
    # CLEANUP
    # --------------------------------------------------

    def close(self):
        """Ensure lifecycle logs are flushed properly."""
        self.lifecycle_logger.close()

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