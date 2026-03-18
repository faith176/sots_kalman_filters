import logging
import time
from typing import Any

from ..schema.Event import Event, make_event
from ..schema.EventGenerator import EventGenerator
from .source_type import *


class EventSource(EventGenerator):

    """
    Base class for all event sources.

    Routes emitted events to partitions depending on the
    lifecycle state of the constituent.
    """

    PARTITION_MAP = {
        "disengaged": None,
        "prepared": None,
        "passive": "observed",
        "active": "observed.validated",
    }

    def __init__(
        self,
        *,
        id: str,
        type: str,
        stream,
        lifecycle
    ):
        self.id = id
        self.type = type
        self.stream = stream
        self.lifecycle = lifecycle

    # --------------------------------------------------
    # Event Construction
    # --------------------------------------------------

    def generate_event(self, params: dict[str, Any]) -> Event:

        return make_event(
            type=self.type,
            src=self.id,
            event_status="observed",
            value=params["value"],
            event_ts=params.get("event_ts", time.time()),
            value_datatype=params.get("value_datatype"),
            value_unit=params.get("value_unit"),
            confidence=params.get("confidence"),
            extras=params.get("extras"),
        )

    # --------------------------------------------------
    # Event Emission
    # --------------------------------------------------

    def emit_event(self, params):

        # snapshot lifecycle state (prevents race conditions)
        state = self.lifecycle.get_state(self.id)

        if not state:
            return None

        belonging_main = state["belonging_main"]

        partition = self.PARTITION_MAP.get(belonging_main)

        # drop event if lifecycle policy says so
        if partition is None:
            logging.debug(
                f"[SOURCE {self.id}] state={belonging_main} → dropped"
            )
            return None

        # create event
        event = self.generate_event(params)
        state = self.lifecycle.get_state(self.id)

        event["extras"]={
            "health": state["health_main"],
            "role": state["belonging_sub"]
        }

        event["partition"] = partition

        ctx = self.lifecycle.constituents.get(self.id)
        if ctx:
            ctx.observed_events += 1

        # publish
        self.stream.add_event(event, partition, self.id)

        logging.debug(
            f"[SOURCE {self.id}] state={belonging_main} → partition={partition}"
        )

        return event