import logging
from ...state_charts.yakindu.timer.timer_service import TimerService


class ConstituentRuntime:

    HEALTH_ORDER = [
        "ideal",
        "defective",
        "faulty",
        "erroneous",
        "malfunctioning",
        "degraded",
        "failed"
    ]

    # ---------------------------------------
    # CLASS-LEVEL STATE MAPPINGS
    # ---------------------------------------

    HEALTH_STATE_MAP = {
        "constituent_lifecycle_orthogonal_states_health_ideal": "ideal",
        "constituent_lifecycle_orthogonal_states_health_defective": "defective",
        "constituent_lifecycle_orthogonal_states_health_faulty": "faulty",
        "constituent_lifecycle_orthogonal_states_health_erroneous": "erroneous",
        "constituent_lifecycle_orthogonal_states_health_malfunctioning": "malfunctioning",
        "constituent_lifecycle_orthogonal_states_health_degraded": "degraded",
        "constituent_lifecycle_orthogonal_states_health_failed": "failed",
    }

    BELONGING_STATE_MAP = {
        "constituent_lifecycle_orthogonal_states_belonging_passive_region0negotiating": "negotiating",
        "constituent_lifecycle_orthogonal_states_belonging_passive_region0avaliable": "available",
        "constituent_lifecycle_orthogonal_states_belonging_active_region0pending_entry": "pending_entry",
        "constituent_lifecycle_orthogonal_states_belonging_active_region0participating_region0full_role": "full_role",
        "constituent_lifecycle_orthogonal_states_belonging_active_region0participating_region0restricted_role": "restricted_role",
        "constituent_lifecycle_orthogonal_states_belonging_active_region0pending_exit": "pending_exit",
        "constituent_lifecycle_orthogonal_states_belonging_disengaged": "disengaged",
        "constituent_lifecycle_orthogonal_states_belonging_prepared": "prepared",
    }

    def __init__(self, statechart_cls, constituent_id):

        self.id = constituent_id
        self.sm = statechart_cls()

        self.timer_service = TimerService()
        self.sm.timer_service = self.timer_service

        self.sm.enter()

        # ---------------------------------------
        # OBSERVABLE STREAMS
        # ---------------------------------------

        self.announce_stream = self.sm.announce_observable
        self.emit_observed_stream = self.sm.emit_observed_observable
        self.emit_validated_stream = self.sm.emit_validated_observable
        self.enable_reconstruction_stream = self.sm.enable_reconstruction_observable
        self.belonging_changed_stream = self.sm.belonging_changed_observable
        self.health_changed_stream = self.sm.health_changed_observable

        self.state = None
        self.update_snapshot()

    # ---------------------------------------
    # INTERNAL EVENT RAISING
    # ---------------------------------------

    def _raise(self, event):

        before = self.state_snapshot()

        getattr(self.sm, event)()
        self.sm.run_cycle()

        self.update_snapshot()

        after = self.state_snapshot()

        logging.info(
            f"[LIFECYCLE] {self.id} "
            f"{before['health_main']}/{before['belonging_sub']} "
            f"→ "
            f"{after['health_main']}/{after['belonging_sub']} "
            f"(event={event})"
        )

    # ---------------------------------------
    # HEALTH NAME
    # ---------------------------------------

    def health_name(self):

        sm = self.sm
        state_vector = sm._Statechart__state_vector
        state = state_vector[1]
        S = sm.State

        for attr, name in self.HEALTH_STATE_MAP.items():
            if state == getattr(S, attr):
                return name

        return "unknown"

    # ---------------------------------------
    # BELONGING SUBSTATE
    # ---------------------------------------

    def belonging_substate(self):

        sm = self.sm
        state_vector = sm._Statechart__state_vector
        state = state_vector[0]
        S = sm.State

        for attr, name in self.BELONGING_STATE_MAP.items():
            if state == getattr(S, attr):
                return name

        return "unknown"

    # ---------------------------------------
    # BELONGING MAIN
    # ---------------------------------------

    def belonging_main(self):

        sub = self.belonging_substate()

        if sub in {"negotiating", "available"}:
            return "passive"

        if sub in {"pending_entry", "full_role", "restricted_role", "pending_exit"}:
            return "active"

        return sub

    # ---------------------------------------
    # CAPABILITY
    # ---------------------------------------

    def capability_level(self):

        main = self.belonging_main()

        if main in {"disengaged", "prepared"}:
            return "not_present"

        if main == "passive":
            return "passive"

        return "restricted" if self.is_restricted() else "full"

    def is_restricted(self):

        try:
            return self.sm.is_state_active(
                self.sm.State.constituent_lifecycle_orthogonal_states_belonging_active_region0participating_region0restricted_role
            )
        except AttributeError:
            return False

    def is_active(self):
        return self.belonging_main() == "active"

    def is_passive(self):
        return self.belonging_main() == "passive"

    def is_present(self):
        return self.belonging_main() not in {"prepared", "disengaged"}

    # ---------------------------------------
    # SNAPSHOT
    # ---------------------------------------

    def update_snapshot(self):

        self.state = {
            "id": self.id,
            "belonging_main": self.belonging_main(),
            "belonging_sub": self.belonging_substate(),
            "health_main": self.health_name(),
            "capability": self.capability_level(),
        }

    def state_snapshot(self):
        return self.state

    # ---------------------------------------
    # BELONGING EVENTS
    # ---------------------------------------

    def prepare(self): self._raise("raise_prepare_for_so_s")
    def disengage(self): self._raise("raise_disengage_from_so_s")
    def join_sos(self): self._raise("raise_join_so_s")
    def leave_sos(self): self._raise("raise_leave_so_s")
    def join_invitation(self): self._raise("raise_join_invitation")
    def join_request(self): self._raise("raise_join_request")
    def admission_rejected(self): self._raise("raise_admission_rejected")
    def exit_denied(self): self._raise("raise_exit_denied")
    def join_constellation(self): self._raise("raise_join_constellation")
    def constellation_stable(self): self._raise("raise_constellation_stable")
    def leave_request(self): self._raise("raise_leave_request")
    def leave_constellation(self): self._raise("raise_leave_constellation")

    def uncertainty_threshold_exceeded(self):
        self._raise("raise_uncertainty_threshold_exceeded")

    # ---------------------------------------
    # HEALTH EVENTS
    # ---------------------------------------

    def degrade(self):
        self._raise("raise_degrade")

    def improve(self):
        self._raise("raise_improve")

    def full_recovery(self):
        self._raise("raise_full_recovery")

    # ---------------------------------------
    # HEALTH NAVIGATION
    # ---------------------------------------

    def ensure_health(self, goal):

        if goal not in self.HEALTH_ORDER:
            raise ValueError(f"Unknown health state: {goal}")

        current = self.health_name()

        if current == goal:
            return True

        if goal == "ideal":
            self.full_recovery()
            return True

        current_idx = self.HEALTH_ORDER.index(current)
        goal_idx = self.HEALTH_ORDER.index(goal)

        if goal_idx > current_idx:
            self.degrade()
        else:
            self.improve()

        return True

    # ---------------------------------------
    # HEALTH HELPERS
    # ---------------------------------------

    def ensure_ideal(self): return self.ensure_health("ideal")
    def ensure_defective(self): return self.ensure_health("defective")
    def ensure_faulty(self): return self.ensure_health("faulty")
    def ensure_erroneous(self): return self.ensure_health("erroneous")
    def ensure_malfunctioning(self): return self.ensure_health("malfunctioning")
    def ensure_degraded(self): return self.ensure_health("degraded")
    def ensure_failed(self): return self.ensure_health("failed")