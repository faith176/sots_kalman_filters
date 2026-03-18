import logging
import threading
from typing import Type

from app.core.schema.EventConsumer import EventConsumer
from app.core.schema.Event import Event
from app.core.communication.Client import Client

__author__ = "Feyi Adesanya"


class EventStream:
    """
    Core event bus for the system.

    Handles publish/subscribe of events across partitions and streams.
    Supports hierarchical partitions such as:

        observed
        observed.validated
        reconstructed

    Also supports wildcard subscriptions:

        observed.*
    """

    def __init__(self, client_type: Type[Client]):

        self.client_type = client_type

        # initial partitions
        self.partitions: dict[str, Client] = {
            "observed": self.client_type(partition="observed"),
            "reconstructed": self.client_type(partition="reconstructed"),
        }

        # wildcard subscriptions
        self._wildcard_subs = []

        self._running = False

    # --------------------------------------------------
    # Partition Management
    # --------------------------------------------------

    def _get_client(self, partition: str, source_id: str) -> Client:
        """
        Retrieve client for a partition.
        Creates the partition dynamically if needed.
        """

        if partition not in self.partitions:

            logging.info(f"[EVENTSTREAM] Creating partition '{partition}'")

            client = self.client_type(partition=partition)
            self.partitions[partition] = client

            # apply wildcard subscriptions
            for consumer, prefix, source_id in self._wildcard_subs:

                if partition.startswith(prefix):

                    logging.debug(
                        f"[EVENTSTREAM] Applying wildcard subscription "
                        f"{prefix}* → {partition}"
                    )

                    client.subscribe_to(source_id, consumer)

        return self.partitions[partition]

    # --------------------------------------------------
    # Publish
    # --------------------------------------------------

    def add_event(self, event: Event, partition: str, source_id: str):

        client = self._get_client(partition, source_id)

        logging.debug(
            f"[EVENTSTREAM] Adding event → {partition}.{source_id}: {event}"
        )
        client.publish(event, source_id)

    # --------------------------------------------------
    # Subscribe
    # --------------------------------------------------

    def subscribe(self, consumer: EventConsumer, partition: str, source_id: str):

        # wildcard subscription
        if partition.endswith(".*"):

            prefix = partition[:-2]

            logging.info(
                f"[EVENTSTREAM] Wildcard subscription: {prefix}.* "
                f"(source={source_id})"
            )

            # subscribe to existing partitions
            for name, client in self.partitions.items():

                if name.startswith(prefix):

                    client.subscribe_to(source_id, consumer)

            # store wildcard for future partitions
            self._wildcard_subs.append((consumer, prefix, source_id))

            return

        # normal subscription
        client = self._get_client(partition, source_id)

        client.subscribe_to(source_id, consumer)

    # --------------------------------------------------
    # Dispatch Loop
    # --------------------------------------------------

    def dispatch(self, timeout: int = 1):

        self._running = True

        while self._running:

            # copy to avoid modification during iteration
            for client in list(self.partitions.values()):

                client.poll_once(timeout=timeout)

    # --------------------------------------------------
    # Start / Stop
    # --------------------------------------------------

    def start(self, timeout: int = 1):

        if self._running:
            return

        self._running = True

        self._thread = threading.Thread(
            target=self.dispatch,
            kwargs={"timeout": timeout},
            daemon=True,
            name="eventstream-dispatch",
        )

        self._thread.start()

    def stop(self):

        logging.info("[EVENTSTREAM] Stopping dispatch loop.")

        self._running = False

        if hasattr(self, "_thread"):

            self._thread.join(timeout=1.0)