import threading
import time
import numpy as np
from messaging.zmq_setup import ZMQPublisher

class SimulatedSensorStream:
    def __init__(self, sensor_id="temp-sensor-001", endpoint = "tcp://*:5555"):
        self.sensor_id = sensor_id
        self.publisher = ZMQPublisher(endpoint=endpoint)
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
    
    def run(self, interval):
        self.running = True
        print(f"[SIMULATOR] Simulating sensor '{self.sensor_id}' every {interval}s")
        while self.running:
            event = self.get_next_event()
            self.publisher.publish(self.sensor_id, event)
            print(f"[SIMULATOR] Sent: {event}")
            time.sleep(interval)

    def stop(self):
        self.running = False
        self.publisher.close()


def start(sensor_id, interval):
    stream = SimulatedSensorStream(sensor_id=sensor_id)
    thread = threading.Thread(target=stream.run, args=(interval,), daemon=True)
    thread.start()
    return stream, thread


if __name__ == "__main__":
    # Start simulator in background thread
    sensor, sim_thread = start("temp-sensor-001", 5.0)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[SIMULATOR] Shutting down...")
        sensor.stop()
        sim_thread.join()
        print("[SIMULATOR] Fully exited.")