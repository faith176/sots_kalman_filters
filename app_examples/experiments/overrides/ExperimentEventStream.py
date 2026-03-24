from app.core.runtime.EventStream import EventStream


class ExperimentEventStream(EventStream):

    def __init__(self, client_type):

        super().__init__(client_type)

        self.partitions = {
            "observed": self.client_type(partition="observed"),
            "reconstructed": self.client_type(partition="reconstructed"),
            "ground_truth": self.client_type(partition="ground_truth"),
        }


    def dispatch(self, timeout: int = 0, once: bool = True):
        """
        Non-blocking dispatch for experiments.
        Processes events once and returns.
        """

        for client in list(self.partitions.values()):

            # keep polling until queue is empty
            while True:
                had_event = client.poll_once(timeout=timeout)

                if not had_event:
                    break