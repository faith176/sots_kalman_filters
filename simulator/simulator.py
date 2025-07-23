import threading
import time
import numpy as np
from messaging.zmq_setup import ZMQPublisher

class SimulatedSensorStream:
    def __init__(self, sensor_id="temp-sensor-001"):
        self.sensor_id = sensor_id
        self.current_value = 20
        self.running = False

    def get_next_value(self):
        self.current_value += np.random.uniform(0.05, 0.05) + np.random.normal(0, 0.1)
        return self.current_value

    def get_next_event(self):
        return {
            "sensor_id": self.sensor_id,
            "timestamp": time.time(),
            "value": self.get_next_value()
        }
    
    def run(self, publisher, interval):
        self.running = True
        print(f"[SIMULATOR] Simulating sensor '{self.sensor_id}' every {interval}s")
        while self.running:
            event = self.get_next_event()
            publisher.publish(self.sensor_id, event)
            print(f"[SIMULATOR] Sent: {event}")
            time.sleep(interval)

    def stop(self):
        self.running = False


def start(endpoint, sensor_id, interval):
    publisher = ZMQPublisher(endpoint=endpoint)
    stream = SimulatedSensorStream(sensor_id=sensor_id)
    thread = threading.Thread(target=stream.run, args=(publisher, interval), daemon=True)
    thread.start()
    return stream, thread, publisher


if __name__ == "__main__":
    # Start simulator in background thread
    sensor, sim_thread, publisher = start("tcp://*:5555", "temp-sensor-001", 5.0)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[SIMULATOR] Shutting down...")
        sensor.stop()
        sim_thread.join()
        print("[SIMULATOR] Fully exited.")