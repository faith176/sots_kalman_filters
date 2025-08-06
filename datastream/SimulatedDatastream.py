import threading
import time
import numpy as np
import zmq
import json
import logging

from messaging.ClientTypes.StreamClient import StreamClient
from datastream.Datastream import DataStream

class SimulatedDatastream(DataStream):
    def __init__(self, sensor_id="temp-sensor-001", name="temp-sensor-001"):
        super().__init__(sensor_id=sensor_id, name=name)
        self.client = StreamClient(name=self.name)
        self.current_value = 20.0
        self.interval = 5.0
        self.running = False
        self.thread = None

        # Subscribe to acks from StreamManager
        self.client.subscribe_to(f"stream_manager.{self.name}")
        self.client.register_handler("stream_manager", self.handle_ack)

    def get_next_value(self):
        self.current_value += np.random.uniform(0.05, 0.05) + np.random.normal(0, 0.1)
        return round(self.current_value, 3)

    def get_next_event(self):
        return {
            "origin": self.name,
            "sensor_id": self.sensor_id,
            "timestamp": time.time(),
            "value": self.get_next_value()
        }

    def handle_ack(self, topic, msg):
        logging.info(f"[{self.name}] ACK received on '{topic}': {msg}")

    def run(self):
        print(f"[SIMULATOR] Started '{self.get_name()}' (every {self.interval}s)")
        while self.running:
            event = self.get_next_event()
            self.client.send_event(event)
            print(f"[SIMULATOR] Sent: {event}")
            time.sleep(self.interval)
        print(f"[SIMULATOR] Stopped '{self.get_name()}'")

    def start(self, interval=5.0):
        if self.running:
            return
        self.interval = interval
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        self.client.close()

    def is_running(self):
        return self.running


def main():
    logging.basicConfig(level=logging.INFO)
    stream = SimulatedDatastream(sensor_id="temp-sensor-001")
    stream.start(interval=2.0)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[MAIN] Shutting down simulated sensor...")
        stream.stop()
        print("[MAIN] Simulator fully exited.")

if __name__ == "__main__":
    main()
