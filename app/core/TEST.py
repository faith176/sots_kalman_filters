from app.core.communication.comm_types.ZMQClient import ZMQClient
from app.core.communication.comm_types.ZMQServer import ZMQServer

from app.core.source.sources.SimulatedEventSource import SimulatedEventSource
from app.core.runtime.EventStream import EventStream
from app.core.runtime.Coordinator import Coordinator
from app.core.processor.EventProcessor import EventProcessor

import time
import logging

from app.core.utils.EventListener.Logger import CSVLogger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

if __name__ == "__main__":

    now = time.time()
    log_run_dir = f"data/logs/main_example/{now}"
    # ---- server ----
    try:
        server = ZMQServer()
        server.run(in_thread=True)
    except Exception:
        logging.info("[RUNNER] ZMQServer already running.")

    # ---- event processor ----
    # cep = EventProcessor(
    #     pattern_cfg="patterns/basic_patterns.json",
    #     run_dir=log_run_dir,
    #     rebuild=True,
    #     log_matches="True",
    # )
    # cep.start()

    # ---- eventstream ----
    stream = EventStream(ZMQClient)
    stream.start()

    # ---- logger ----
    logger = CSVLogger(log_run_dir)
    for partition in stream.partitions.keys():
            stream.subscribe(logger, partition, "*")

    # ---- coordinator ----
    coordinator = Coordinator(
        event_stream=stream,
        sources_config_path="configs/sources.json",
        predictors_config_path="configs/predictors.json",
    )
    coordinator.start()

    # ---- simulated source ----
    src_1 = SimulatedEventSource(
        id="sim-1",
        type="speed",
        stream=stream,
        interval=1.0,
        value_unit="km/hr",
    )
    src_1.start()

    src_2 = SimulatedEventSource(
        id="sim-2",
        type="speed",
        stream=stream,
        interval=1.0,
        value_unit="km/hr",
    )
    src_2.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("[RUNNER] Shutting down...")
        src_1.stop()
        src_2.stop()
        coordinator.stop()
        logger.stop()
        # cep.stop()
        server.stop()
