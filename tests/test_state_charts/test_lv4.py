from app.core.runtime.ConstituentRuntime import ConstituentRuntime
from app.state_charts.lv4 import Statechart
import time

# python -m tests.test_state_charts.test_lv4

STEP_DELAY = 0.25
OBSERVE_DELTA = 1


class ConstituentRuntimeTester:

    def __init__(self):
        self.setup()

    # --------------------------------------------------
    # SETUP / RESET
    # --------------------------------------------------

    def setup(self):
        """Reset runtime before each test"""
        self.runtime = ConstituentRuntime(Statechart, "DT1")

    # --------------------------------------------------
    # TIMING HELPERS
    # --------------------------------------------------

    def wait_step(self):
        time.sleep(STEP_DELAY)

    def wait_delta(self):
        time.sleep(OBSERVE_DELTA)

    # --------------------------------------------------
    # PRINT STATE
    # --------------------------------------------------

    def print_state(self, label):

        state = self.runtime.state_snapshot()

        print("-----", label, "-----")
        print("ID:", state["id"])
        print("Belonging (main):", state["belonging_main"])
        print("Belonging (sub):", state["belonging_sub"])
        print("Health:", state["health_main"])
        print("Capability:", state["capability"])
        print()

    # --------------------------------------------------
    # ASSERT STATE
    # --------------------------------------------------

    def assert_state(self, main=None, sub=None, health=None):

        s = self.runtime.state_snapshot()

        if main:
            assert s["belonging_main"] == main

        if sub:
            assert s["belonging_sub"] == sub

        if health:
            assert s["health_main"] == health

    # --------------------------------------------------
    # STATE PREPARATION HELPERS
    # --------------------------------------------------

    def go_to_prepared(self):
        self.runtime.prepare()
        self.wait_step()

    def go_to_passive(self):
        self.go_to_prepared()
        self.runtime.join_sos()
        self.wait_step()

    def go_to_active(self):

        self.go_to_passive()

        self.runtime.join_invitation()
        self.wait_step()

        self.runtime.join_constellation()
        self.wait_step()

        self.wait_delta()

    # --------------------------------------------------
    # FULL LIFECYCLE TEST
    # --------------------------------------------------

    def test_full_belonging_lifecycle(self):

        self.setup()

        print("\n===== FULL LIFECYCLE =====\n")

        self.print_state("Initial")

        # disengaged → prepared
        self.runtime.prepare()
        self.wait_step()

        self.assert_state("prepared")
        self.print_state("Prepared")

        # prepared → passive
        self.runtime.join_sos()
        self.wait_step()

        self.assert_state("passive", "available")
        self.print_state("Available")

        # negotiation
        self.runtime.join_invitation()
        self.wait_step()

        self.assert_state("passive", "negotiating")
        self.print_state("Negotiating")

        # rejection
        self.runtime.admission_rejected()
        self.wait_step()

        self.assert_state("passive", "available")
        self.print_state("Back to Available")

        # accept negotiation
        self.runtime.join_invitation()
        self.wait_step()

        self.runtime.join_constellation()
        self.wait_step()

        self.assert_state("active", "pending_entry")
        self.print_state("Pending Entry")

        self.wait_delta()

        self.print_state("Participating")

    # --------------------------------------------------
    # ENFORCEMENT TESTS
    # --------------------------------------------------

    def test_passive_leave_sos(self):

        self.setup()

        print("\n===== PASSIVE → PREPARED ENFORCEMENT =====")

        self.go_to_passive()

        self.runtime.leave_sos()
        self.wait_step()

        self.assert_state("prepared")

        self.print_state("Leave SoS from Passive")

    def test_failed_forces_prepared(self):

        self.setup()

        print("\n===== FAILED → PREPARED ENFORCEMENT =====")

        self.go_to_passive()

        self.runtime.component_deviation()
        self.runtime.defect_activated()
        self.runtime.fault_exercised()
        self.runtime.error_propagation()
        self.runtime.service_impact()
        self.runtime.service_threshold()

        self.wait_step()

        self.assert_state("prepared")

        self.print_state("Forced Prepared")

    def test_leave_request_pending_exit(self):

        self.setup()

        print("\n===== LEAVE REQUEST FROM ACTIVE =====")

        self.go_to_active()

        self.runtime.leave_request()
        self.wait_step()

        self.assert_state("active", "pending_exit")

        self.print_state("Pending Exit")

    def test_join_blocked_if_failed(self):

        self.setup()

        print("\n===== JOIN BLOCKED WHEN FAILED =====")

        self.go_to_prepared()

        self.runtime.component_deviation()
        self.runtime.defect_activated()
        self.runtime.fault_exercised()
        self.runtime.error_propagation()
        self.runtime.service_impact()
        self.runtime.service_threshold()

        self.wait_step()

        self.runtime.join_sos()
        self.wait_step()

        self.assert_state("prepared")

        self.print_state("Join Blocked")

    def test_negotiation_requires_ideal(self):

        self.setup()

        print("\n===== NEGOTIATION GUARD =====")

        self.go_to_passive()

        self.runtime.component_deviation()
        self.wait_step()

        self.runtime.join_request()
        self.wait_step()

        self.assert_state("passive", "available")

        self.print_state("Join Request Blocked")

    def test_restricted_to_full_recovery(self):

        self.setup()

        print("\n===== RESTRICTED ROLE RECOVERY =====")

        self.go_to_active()

        self.runtime.component_deviation()
        self.runtime.defect_activated()
        self.runtime.fault_exercised()

        self.wait_step()

        self.print_state("Restricted Role")

        self.runtime.recover()
        self.wait_step()

        self.print_state("Recovered to Full Role")



    def test_exit_denied_returns_to_participating(self):

        self.setup()

        print("\n===== EXIT DENIED RETURNS TO PARTICIPATING =====")

        # move to participating
        self.go_to_active()

        self.print_state("Participating")

        # request exit
        self.runtime.leave_request()
        self.wait_step()

        self.assert_state("active", "pending_exit")
        self.print_state("Pending Exit")

        # deny exit BEFORE delta transition
        self.runtime.exit_denied()
        self.wait_step()

        # should return to participating
        self.assert_state("active", "full_role")

        self.print_state("Exit Denied → Back to Participating")


    def test_ensure_prepared_from_active(self):

        self.setup()

        print("\n===== ENSURE PREPARED FROM ACTIVE =====")

        self.go_to_active()

        self.print_state("Active")

        success = self.runtime.ensure_prepared()

        self.wait_step()

        assert success is True

        self.assert_state("prepared")

        self.print_state("Prepared")


    def test_ensure_passive(self):

        self.setup()

        print("\n===== ENSURE PASSIVE =====")

        self.go_to_prepared()

        self.print_state("Prepared")

        success = self.runtime.ensure_passive()

        self.wait_step()

        assert success is True

        self.assert_state("passive", "available")

        self.print_state("Passive")


    def test_ensure_active(self):

        self.setup()

        print("\n===== ENSURE ACTIVE =====")

        self.go_to_passive()

        self.print_state("Passive")

        success = self.runtime.ensure_active()

        self.wait_step()

        assert success is True

        self.assert_state("active", "pending_entry")

        self.print_state("Pending Entry")

        self.wait_delta()

        self.print_state("Participating")

    def test_ensure_disengaged(self):

        self.setup()

        print("\n===== ENSURE DISENGAGED =====")

        self.go_to_active()

        self.print_state("Active")

        success = self.runtime.ensure_disengaged()

        self.wait_step()

        assert success is True

        self.assert_state("disengaged")

        self.print_state("Disengaged")


    def test_ensure_active_blocked_by_health(self):

        self.setup()

        print("\n===== ENSURE ACTIVE BLOCKED BY HEALTH =====")

        # move to passive
        self.go_to_passive()

        self.assert_state("passive", "available")

        self.print_state("Passive (Available)")

        # degrade health so join_request guard fails
        self.runtime.component_deviation()
        self.runtime.defect_activated()
        self.runtime.fault_exercised()
        self.runtime.error_propagation()

        self.wait_step()

        self.print_state("Health Degraded")

        # attempt to force active
        success = self.runtime.ensure_active()

        # ensure lifecycle function reports failure
        assert success is False

        # verify state did not change
        self.assert_state("passive", "available")

        self.print_state("Active Attempt Blocked")


    

    # --------------------------------------------------
    # RUN ALL TESTS
    # --------------------------------------------------

    def run_all_tests(self):

        self.test_full_belonging_lifecycle()
        self.test_passive_leave_sos()
        self.test_failed_forces_prepared()
        self.test_leave_request_pending_exit()
        self.test_join_blocked_if_failed()
        self.test_negotiation_requires_ideal()
        self.test_restricted_to_full_recovery()
        self.test_exit_denied_returns_to_participating()
        self.test_ensure_prepared_from_active()
        self.test_ensure_passive()
        self.test_ensure_active()
        self.test_ensure_disengaged()
        self.test_ensure_active_blocked_by_health()

        print("\nAll tests complete.\n")


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    tester = ConstituentRuntimeTester()

    tester.run_all_tests()


if __name__ == "__main__":
    main()