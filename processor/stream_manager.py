# Add logic for tracking when timestamps are missing and need to be imputed
import threading
import time
import zmq
from utils.schema_validator import validate_config, validate_event
from utils.config_loader import load_filters_from_config
from filter.confidence import compute_confidence
from messaging.zmq_setup import ZMQPublisher, ZMQSubscriber

class StreamManager:
    def __init__(self, config_path, endpoint="tcp://*:7777"):
        self.config = validate_config(config_path)
        self.filters = load_filters_from_config(config_path)
        self.sensor_to_endpoint = {
            sensor["sensor_id"]: sensor["source_endpoint"]
            for sensor in self.config["sensors"]
        }
        self.sensor_metadata = {
            sensor["sensor_id"]: {
                "units": sensor.get("units", "unknown"),
                "stream_type": sensor.get("stream_type", "unspecified"),
                "sampling_interval_sec": sensor.get("sampling_interval_sec", 1),
            }
            for sensor in self.config["sensors"]
        }
        self.last_seen = {sensor_id: 0 for sensor_id in self.sensor_to_endpoint}


        self.endpoint = endpoint
        self.publisher = ZMQPublisher(endpoint=endpoint)
        self.subscribers = {}
        self.poller = zmq.Poller()
        self._setup_subscribers()

    def _setup_subscribers(self):
        unique_endpoints = set(self.sensor_to_endpoint.values())
        for endpoint in unique_endpoints:
            subscriber = ZMQSubscriber(endpoint=endpoint)
            self.subscribers[endpoint] = subscriber
            self.poller.register(subscriber.socket, zmq.POLLIN)
            print(f"[STREAM MANAGER] Subscribed to {endpoint}")

    def process_once(self):
        events = dict(self.poller.poll(timeout=1000))
        for endpoint, subscriber in self.subscribers.items():
            if subscriber.socket in events:
                topic, event = subscriber.receive()
                self._process_event(event)

    def _process_event(self, event):
        sensor_id = event["sensor_id"]
        value = event["value"]
        timestamp = event["timestamp"]
        self.last_seen[sensor_id] = timestamp
        meta = self.sensor_metadata.get(sensor_id, {})

        print(f"[STREAM MANAGER] Received from {sensor_id}: {value} at timestamp {timestamp}")

        if sensor_id not in self.filters:
            print(f"[ERROR] No filter configured for sensor: {sensor_id}")
            return

        kf = self.filters[sensor_id]
        kf.predict()
        kf.update(value)

        confidence = compute_confidence(kf.get_covariance())
        filtered_event = {
            "streamId": sensor_id,
            "timestamp": timestamp,
            "filteredMeasurement": kf.get_value(),
            "quality": {
                "imputed": False,
                "confidence": confidence
            },
            "streamInfo": {
                "streamType": meta.get("stream_type", "unspecified"),
                "unit": meta.get("units", "unspecified"),
                "filterSource": kf.get_type()
            }
        }

        validate_event(filtered_event)
        self.publisher.publish(sensor_id, filtered_event)
        print(f"[STREAM MANAGER] Published: {filtered_event}")

    def start(self):
        print(f"[STREAM MANAGER] Running. Output publishing on endpoint {self.endpoint}")
        self._running = True
        try:
            while self._running:
                self.process_once()
        except KeyboardInterrupt:
            print("[STREAM MANAGER] Shutting down...")
        finally:
            self._shutdown()

    def stop(self):
        self._running = False
        self.publisher.close()

    def _shutdown(self):
        for subscriber in self.subscribers.values():
            subscriber.close()
        self.publisher.close()


if __name__ == "__main__":
    stream_manager = StreamManager("config/config.json")
    stream_thread = threading.Thread(target=stream_manager.start)
    stream_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[STREAM MANAGER] Shutting down...")
        stream_manager.stop()
        stream_thread.join()
        print("[STREAM MANAGER] Fully exited.")