import logging
import time
from typing import Dict
from dataclasses import dataclass, field

from . import LifecycleLogger

# Helpers
class ExperimentClock:
    start_time = time.time()

    @staticmethod
    def now():
        return time.time() - ExperimentClock.start_time

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