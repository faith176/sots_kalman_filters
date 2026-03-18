class ExperimentController:

    def __init__(self, lifecycle, config):

        self.lifecycle = lifecycle
        self.config = config
        self.rng = config.rng()

    def step(self):

        for source_id in self.lifecycle.constituents:

            runtime = self.lifecycle.get_runtime(source_id)

            if not runtime:
                continue

            self._update_participation(runtime)
            self._update_health(runtime)


    def _update_participation(self, runtime):

        r = self.rng.random()

        state = runtime.state_snapshot()

        if runtime.is_active():

            if r < self.config.p_leave:
                runtime.leave_sos()

        else:

            if r < self.config.p_join:
                runtime.join_sos()


    def _update_health(self, runtime):

        r = self.rng.random()

        if r < self.config.p_degrade:
            runtime.ensure_degraded()

        elif r < self.config.p_degrade + self.config.p_recover:
            runtime.ensure_ideal()