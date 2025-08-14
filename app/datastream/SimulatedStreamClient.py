import time
import threading
import numpy as np
import logging
from messaging.ClientTypes.StreamClient import StreamClient

class SimulatedStreamClient:
    def __init__(self, sensor_id: str, interval: float = 1.0, unit: str = "°C"):
        self.sensor_id = sensor_id
        self.interval = interval
        self.unit = unit
        self.running = False
        self.client = StreamClient(name=f"SimClient-{sensor_id}")
        self._value = 20.0  # Initial simulated value
        self.thread = None

    def _generate_value(self):
        """Simulate noisy value."""
        self._value += np.random.normal(loc=0.0, scale=0.1)
        return round(self._value, 3)

    def _build_event(self, value: float) -> dict:
        """Builds a JSON event."""
        return {
            "stream_id": self.sensor_id,
            "timestamp": time.time(),
            "value": value,
            "unit": self.unit
        }

    def _run_loop(self):
        logging.info(f"[SimulatedSensorClient] Starting for '{self.sensor_id}'")
        while self.running:
            value = self._generate_value()
            event = self._build_event(value)
            topic = f"data.{self.sensor_id}"
            self.client.send_event(event, topic=topic)
            time.sleep(self.interval)

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            logging.info(f"[SimulatedSensorClient] Started '{self.sensor_id}'")

    def stop(self):
        if self.running:
            self.running = False
            self.thread.join()
            self.client.close()
            logging.info(f"[SimulatedSensorClient] Stopped '{self.sensor_id}'")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    sensor = SimulatedStreamClient("temp-sensor-001", interval=2.0)

    try:
        sensor.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("[MAIN] Interrupt received. Shutting down...")
        sensor.stop()
