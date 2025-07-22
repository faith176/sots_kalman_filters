import threading
import time
import numpy as np
from publish.zmq_setup import ZMQPublisher

class SimulatedSensorStream:
    def __init__(self, sensor_id="sensor-A", amplitude=1.0, noise_std=0.1):
        self.sensor_id = sensor_id
        self.amplitude = amplitude
        self.noise_std = noise_std
        self.t = 0.0
        self.running = False

    def get_next_value(self):
        value = self.amplitude * np.sin(self.t) + np.random.normal(0, self.noise_std)
        self.t += 0.1
        return value

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


def start(endpoint: str, sensor_id: str, interval: float):
    publisher = ZMQPublisher(endpoint=endpoint)
    stream = SimulatedSensorStream(sensor_id=sensor_id)
    thread = threading.Thread(target=stream.run, args=(publisher, interval), daemon=True)
    thread.start()
    return stream, thread, publisher
