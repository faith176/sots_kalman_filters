from app.core.runtime.ConstituentController import ConstituentController
from app.state_charts.lv4_adaptive import Statechart
import time

# python -m tests.test_state_charts.test_constituent_controller

STEP_DELAY = 0.01


class ConstituentControllerTester:

    def __init__(self):
        self.setup()

    def setup(self):
        self.runtime = ConstituentController(Statechart, "DT1")

    def wait(self):
        time.sleep(STEP_DELAY)


    def print_state(self, label):
        s = self.runtime.state_snapshot()
        print(f"\n--- {label} ---")
        print(s)

    def assert_sub(self, expected):
        actual = self.runtime.belonging_substate()
        assert actual == expected, f"Expected {expected}, got {actual}"

    def assert_participating(self):
        actual = self.runtime.belonging_substate()
        assert actual in {"full_role", "restricted_role"}, \
            f"Expected participating, got {actual}"
        
    def assert_health(self, expected):
        actual = self.runtime.health_name()
        assert actual == expected, f"Expected {expected}, got {actual}"


    def test_ensure_available(self):
        self.setup()

        self.runtime.ensure_available()
        self.wait()

        self.assert_sub("available")
        self.print_state("Available")

    def test_ensure_negotiating(self):
        self.setup()

        self.runtime.ensure_negotiating()
        self.wait()

        self.assert_sub("negotiating")
        self.print_state("Negotiating")

    def test_ensure_participating(self):
        self.setup()

        self.runtime.ensure_participating()
        self.wait()

        self.assert_participating()
        self.print_state("Participating")

    def test_ensure_prepared(self):
        self.setup()

        self.runtime.ensure_prepared()
        self.wait()

        self.assert_sub("prepared")
        self.print_state("Prepared")

    def test_ensure_disengaged(self):
        self.setup()

        self.runtime.ensure_disengaged()
        self.wait()

        self.assert_sub("disengaged")
        self.print_state("Disengaged")

    def test_full_path_to_participating(self):
        self.setup()

        print("\n===== PATH TO PARTICIPATING =====")

        self.runtime.ensure_participating()
        self.wait()

        self.assert_participating()
        self.print_state("Reached Participating")


    def test_policy_completeness(self):
        states = set(self.runtime.BELONGING_STATE_MAP.values())

        for goal, mapping in self.runtime.BELONGING_POLICY.items():
            missing = states - set(mapping.keys())
            assert not missing, f"{goal} missing: {missing}"



    def test_all_goal_reachability(self):

        states = (
            set(self.runtime.BELONGING_STATE_MAP.values())
            - {"restricted_role", "full_role", "pending_entry", "pending_exit"}
        ) | {"participating"}

        for start in states:
            for goal in states:
                print(f"{start} -> {goal}")

                self.setup()

                # move to start
                self.runtime.ensure_belonging(start)
                time.sleep(self.runtime.sm.DELTA +0.05)

                # try to reach goal
                success = self.runtime.ensure_belonging(goal)
                assert success is True, f"{start} → {goal} failed"
                self.wait()

                # validate result
                if goal == "participating":
                    self.assert_participating()
                else:
                    self.assert_sub(goal)

        print("\n Reachability test passed")


    def test_health_degradation_path(self):
        self.setup()

        print("\n===== HEALTH DEGRADATION =====")

        order = self.runtime.HEALTH_ORDER

        for expected in order[1:]:
            self.runtime.degrade()
            self.wait()
            self.assert_health(expected)
            self.print_state(f"Health → {expected}")


    def test_health_recovery_path(self):
        self.setup()

        print("\n===== HEALTH RECOVERY =====")

        # go to worst state
        for _ in range(len(self.runtime.HEALTH_ORDER) - 1):
            self.runtime.degrade()

        self.wait()

        reversed_order = list(reversed(self.runtime.HEALTH_ORDER[:-1]))

        for expected in reversed_order:
            self.runtime.improve()
            self.wait()
            self.assert_health(expected)
            self.print_state(f"Recovered → {expected}")

    def test_full_recovery(self):
        self.setup()

        print("\n===== FULL RECOVERY =====")

        # degrade fully
        for _ in range(len(self.runtime.HEALTH_ORDER) - 1):
            self.runtime.degrade()

        self.wait()

        self.runtime.full_recovery()
        self.wait()

        self.assert_health("ideal")
        self.print_state("Fully Recovered")


    def test_ensure_health(self):
        self.setup()

        print("\n===== ENSURE HEALTH =====")

        # move to degraded
        for _ in range(5):
            self.runtime.degrade()

        self.wait()
        self.assert_health("degraded")

        # ensure upward
        self.runtime.ensure_health("ideal")
        self.wait()
        self.assert_health("ideal")

        # ensure downward
        self.runtime.ensure_health("faulty")
        self.wait()
        self.assert_health("faulty")

        # ensure downward
        self.runtime.ensure_health("malfunctioning")
        self.wait()
        self.assert_health("malfunctioning")

        # ensure upwards
        self.runtime.ensure_health("defective")
        self.wait()
        self.assert_health("defective")

    def test_health_boundaries(self):
        self.setup()

        print("\n===== HEALTH BOUNDARIES =====")

        # already ideal → improve should not break
        self.runtime.improve()
        self.wait()
        self.assert_health("ideal")

        # go to failed
        for _ in range(len(self.runtime.HEALTH_ORDER) - 1):
            self.runtime.degrade()

        self.wait()
        self.assert_health("failed")

        # further degrade shouldn't break
        self.runtime.degrade()
        self.wait()
        self.assert_health("failed")



    def test_passive_failed_forces_prepared(self):
        self.setup()

        print("\n===== PASSIVE + FAILED → PREPARED =====")

        self.runtime.ensure_available()
        self.wait()

        self.runtime.ensure_health("failed")
        self.wait()

        self.assert_sub("prepared")
        self.print_state("Forced Prepared from Passive")
    
    def test_active_failed_forces_prepared(self):
        self.setup()

        print("\n===== ACTIVE + FAILED → PREPARED =====")

        self.runtime.ensure_participating()
        self.wait()

        self.runtime.ensure_health("failed")
        self.wait()

        self.assert_sub("prepared")
        self.print_state("Forced Prepared from Active")

    def test_join_blocked_when_failed(self):
        self.setup()

        print("\n===== JOIN BLOCKED WHEN FAILED =====")

        self.runtime.ensure_prepared()
        self.wait()

        self.runtime.ensure_health("failed")
        self.wait()

        self.runtime.ensure_available()
        self.wait()

        # should remain prepared
        self.assert_sub("prepared")
        self.print_state("Join Blocked")

    def test_negotiation_requires_faulty_or_better(self):
        self.setup()

        print("\n===== NEGOTIATION GUARD =====")

        self.runtime.ensure_available()
        self.wait()

        self.runtime.ensure_health("erroneous")  # worse than faulty
        self.wait()

        self.runtime.ensure_negotiating()
        self.wait()

        # should stay available
        self.assert_sub("available")
        self.print_state("Negotiation Blocked")


    def test_participating_full_role_when_healthy(self):
        self.setup()

        print("\n===== FULL ROLE WHEN HEALTHY =====")

        self.runtime.ensure_health("faulty")
        self.runtime.ensure_participating()
        self.wait()

        self.assert_sub("full_role")
        self.print_state("Full Role")

    def test_participating_restricted_when_unhealthy(self):
        self.setup()

        print("\n===== RESTRICTED ROLE WHEN UNHEALTHY =====")
        
        self.runtime.ensure_participating()
        self.runtime.ensure_health("erroneous")
        self.wait()

        self.assert_sub("restricted_role")
        self.print_state("Restricted Role")

    def test_degraded_triggers_pending_exit(self):
        self.setup()

        print("\n===== DEGRADED → AVAILABLE =====")
        self.runtime.ensure_participating()
        self.wait()

        self.runtime.ensure_health("degraded")
        time.sleep(self.runtime.sm.DELTA +0.05)

        self.assert_sub("available")
        self.print_state("Pending Exit Triggered to Available")


    def run_all_tests(self):

        self.test_health_degradation_path()
        self.test_health_recovery_path()
        self.test_full_recovery()
        self.test_ensure_health()
        self.test_health_boundaries()

        self.test_policy_completeness()

        self.test_ensure_available()
        self.test_ensure_negotiating()
        self.test_ensure_participating()
        self.test_ensure_prepared()
        self.test_ensure_disengaged()

        self.test_full_path_to_participating()
        self.test_all_goal_reachability()

        self.test_passive_failed_forces_prepared()
        self.test_active_failed_forces_prepared()
        self.test_join_blocked_when_failed()
        self.test_negotiation_requires_faulty_or_better()
        self.test_participating_full_role_when_healthy()
        self.test_participating_restricted_when_unhealthy()
        self.test_degraded_triggers_pending_exit()

        print("\n ALL TESTS PASSED\n")

def main():
    tester = ConstituentControllerTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()