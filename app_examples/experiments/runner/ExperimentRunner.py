from app_examples.experiments.overrides.ExperimentOrchestrator import ExperimentOrchestrator
from app_examples.experiments.runner.ExperimentClock import SimulationClock
from app_examples.experiments.runner.Scenarios import *
def main():
    config_path = "app_examples/experiments/configs/config.json"

    clock = SimulationClock()
    scenario = PeriodicDropScenario()

    orchestrator = ExperimentOrchestrator(
        config_path=config_path,
        scenario=scenario,
        clock=clock
    )
    orchestrator.run(T=25)

if __name__ == "__main__":
    main()