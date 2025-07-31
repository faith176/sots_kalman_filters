import threading
import time
import numpy as np
from messaging.zmq_setup import ZMQPublisher
from datastream.datastream_base import DataStream

class SimulatedSensorStream(DataStream):
    def __init__(self, sensor_id="temp-sensor-001", endpoint="tcp://*:5555"):
        self.sensor_id = sensor_id
        self.publisher = ZMQPublisher(endpoint=endpoint)
        self.current_value = 20
        self.running = False
        self.thread = None
        self.interval = 5.0

    def get_next_value(self):
        self.current_value += np.random.uniform(0.05, 0.05) + np.random.normal(0, 0.1)
        return self.current_value

    def get_next_event(self):
        return {
            "sensor_id": self.sensor_id,
            "timestamp": time.time(),
            "value": self.get_next_value()
        }

    def _run_loop(self):
        print(f"[SIMULATOR] Simulating sensor '{self.sensor_id}' every {self.interval}s")
        while self.running:
            event = self.get_next_event()
            self.publisher.publish(self.sensor_id, event)
            print(f"[SIMULATOR] Sent: {event}")
            time.sleep(self.interval)

    def start(self, interval):
        self.interval = interval
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.publisher.close()

    def is_running(self):
        return self.running

    def join(self):
        if self.thread:
            self.thread.join()

def main():
    stream = SimulatedSensorStream(sensor_id="temp-sensor-001")
    stream.start(interval=2.0)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[SIMULATOR] Stopping stream...")
        stream.stop()
        stream.join()
        print("[SIMULATOR] Fully exited.")


if __name__ == "__main__":
    main()
