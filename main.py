import threading
import time
from processor.stream_manager import StreamManager
from simulator.simulator import start

if __name__ == "__main__":
    # Start simulator in background thread
    sensor, sim_thread, publisher = start("tcp://*:5555", "temp-sensor-001", 1.0)

    # Start StreamManager in background
    stream_manager = StreamManager("config/config.json")
    stream_thread = threading.Thread(target=stream_manager.start)
    stream_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[MAIN] Shutting down...")
        sensor.stop()
        stream_manager.stop()
        stream_thread.join()
        sim_thread.join()
        print("[MAIN] Fully exited.")
