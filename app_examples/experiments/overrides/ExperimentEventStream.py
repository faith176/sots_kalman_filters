from app.core.runtime.EventStream import EventStream


class ExperimentEventStream(EventStream):

    def __init__(self, client_type):

        super().__init__(client_type)
        
        self.partitions["ground_truth"] = self.client_type(
            partition="ground_truth"
        )
