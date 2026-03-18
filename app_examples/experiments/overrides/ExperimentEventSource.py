from app.core.source.EventSource import EventSource


class ExperimentEventSource(EventSource):

    def emit_event(self, params):

        state = self.lifecycle.get_state(self.id)

        if not state:
            return None

        belonging_main = state["belonging_main"]

        partition = self.PARTITION_MAP.get(belonging_main)

        if partition is None:
            return None

        # -------------------------
        # create event
        # -------------------------

        event = self.generate_event(params)

        event["extras"] = {
            "health": state["health_main"],
            "role": state["belonging_sub"]
        }

        # -------------------------
        # emit ground truth
        # -------------------------

        truth_event = dict(event)
        truth_event["partition"] = "ground_truth"

        self.stream.add_event(
            truth_event,
            "ground_truth",
            self.id
        )

        # -------------------------
        # emit observed event
        # -------------------------

        event["partition"] = partition

        self.stream.add_event(
            event,
            partition,
            self.id
        )

        return event