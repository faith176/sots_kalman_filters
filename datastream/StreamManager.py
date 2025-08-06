import logging
import threading
import time

from utils.config_loader import instantiate_filter, load_filter_templates, load_stream_metadata
from filter.Confidence import compute_confidence
from messaging.ClientTypes.StreamClient import StreamClient

class StreamManager:
    def __init__(self, filter_config_path="config/filters.json", stream_config_path="config/streams.json"):
        self.client = StreamClient(name="StreamManager")
        self.running = False
        self.thread = None

        # Subscribe to all relevant topics
        self.client.subscribe_to("data.")
        self.client.subscribe_to("command.")
        self.client.subscribe_to("config.")

        # Register handlers
        self.client.register_handler("data", self.handle_data)
        self.client.register_handler("command", self.handle_command)
        self.client.register_handler("config", self.handle_config)

        # Internal state
        self.filter_templates = load_filter_templates(filter_config_path)
        self.stream_metadata = load_stream_metadata(stream_config_path)
        self.stream_filters = {}

        # Initialize any streams with pre-assigned filters
        self._initialize_filters()

    def _initialize_filters(self):
        for stream_id, meta in self.stream_metadata.items():
            template_id = meta.get("filter_template")
            if template_id and template_id in self.filter_templates:
                self.stream_filters[stream_id] = instantiate_filter(self.filter_templates[template_id])
                logging.info(f"[StreamManager] Initialized stream '{stream_id}' with filter '{template_id}'")
            elif template_id:
                logging.warning(f"[StreamManager] Template '{template_id}' for stream '{stream_id}' not found. Awaiting dynamic assignment.")
            else:
                logging.info(f"[StreamManager] Stream '{stream_id}' initialized with no filter.")

    # -- Filter Registration --

    def register_filter_template(self, template_id, params):
        self.filter_templates[template_id] = params
        logging.info(f"[StreamManager] Registered new filter template '{template_id}'")

    def register_filter_for_stream(self, stream_id, template_id):
        if template_id not in self.filter_templates:
            logging.error(f"[StreamManager] Cannot assign unknown filter template '{template_id}'")
            return
        self.stream_filters[stream_id] = instantiate_filter(self.filter_templates[template_id])
        logging.info(f"[StreamManager] Assigned filter '{template_id}' to stream '{stream_id}'")

    def deregister_filter_for_stream(self, stream_id):
        if stream_id in self.stream_filters:
            del self.stream_filters[stream_id]
            logging.info(f"[StreamManager] Deregistered filter from stream '{stream_id}'")
        else:
            logging.warning(f"[StreamManager] No filter to remove for stream '{stream_id}'")

    # -- Stream Registration --

    def register_stream(self, stream_id, metadata: dict):
        self.stream_metadata[stream_id] = metadata
        logging.info(f"[StreamManager] Registered new stream '{stream_id}'")
        if "filter_template" in metadata:
            self.register_filter_for_stream(stream_id, metadata["filter_template"])

    def deregister_stream(self, stream_id):
        self.stream_metadata.pop(stream_id, None)
        self.deregister_filter_for_stream(stream_id)
        logging.info(f"[StreamManager] Removed stream '{stream_id}'")

    # -- Event Handlers --

    def handle_data(self, topic, msg):
        name = topic.split("data.")[1]
        logging.info(f"[StreamManager] Received data from {name}: {msg}")

        stream_id = msg.get("sensor_id")
        if not stream_id or stream_id not in self.stream_metadata:
            logging.warning(f"[StreamManager] Unknown or unregistered stream '{stream_id}'")
            return

        kf = self.stream_filters.get(stream_id)
        if not kf:
            logging.warning(f"[StreamManager] No filter assigned to stream '{stream_id}'")
            return

        value = msg["value"]
        timestamp = msg["timestamp"]

        # Filter operations
        kf.predict()
        kf.update(value)

        confidence = compute_confidence(kf.get_covariance())
        filtered_event = {
            "origin": "StreamManager",
            "streamId": stream_id,
            "timestamp": timestamp,
            "filteredMeasurement": kf.get_value(),
            "quality": {
                "imputed": False,
                "confidence": confidence
            },
            "streamInfo": {
                "streamType": self.stream_metadata.get(stream_id, {}).get("stream_type", "unknown"),
                "unit": self.stream_metadata.get(stream_id, {}).get("units", "unknown"),
                "filterSource": kf.get_type()
            }
        }

        topic = f"CEP.{stream_id}"
        self.client.send_event(filtered_event, topic=topic)
        logging.debug(f"[StreamManager] Published filtered event to '{topic}': {filtered_event}")

    def handle_command(self, topic, msg):
        logging.info(f"[StreamManager] Received command: {msg}")
        # TODO: Implement command logic

    def handle_config(self, topic, msg):
        logging.info(f"[StreamManager] Received config update: {msg}")
        # TODO: Handle live config updates

    # -- Lifecycle Management --

    def run(self):
        self.client.join()
        self.running = True
        logging.info("[StreamManager] Running...")
        try:
            self.client.subscribe()
        except Exception as e:
            logging.error(f"[StreamManager] Subscribe error: {e}")
        finally:
            self.running = False

    def start(self):
        if not self.running:
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            logging.info("[StreamManager] Started in background thread.")

    def stop(self):
        logging.info("[StreamManager] Stopping...")
        self.running = False
        if self.client:
            self.client.close()
        if self.thread:
            self.thread.join()
        logging.info("[StreamManager] Fully stopped.")

# --- Main Entry ---

def main():
    logging.basicConfig(level=logging.DEBUG)
    manager = StreamManager(
        filter_config_path="config/filters.json",
        stream_config_path="config/streams.json"
    )
    manager.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[MAIN] Caught Ctrl+C. Shutting down StreamManager...")
        manager.stop()
        print("[MAIN] StreamManager fully exited.")

if __name__ == "__main__":
    main()


# class StreamManager:
#     def __init__(self, config_path):
#         self.config_path = config_path
#         self.filters = load_filters_from_config(config_path)
#         self.client = StreamClient(alias="streammanager")
#         self.client.on_event_received(self.handle_received_event)

#         self.sensor_metadata = {}
#         self.last_seen = {}
#         self.datastreams = {}

#         # Ensure StreamManager subscribes to all *.data topics from the start
#         self.client._subscriber.setsockopt_string(zmq.SUBSCRIBE, "data.")
#         print("[STREAM MANAGER] Subscribed to all topics ending with '.data'")

#         for sensor_id in self.filters:
#             self.last_seen[sensor_id] = 0

#         print("[STREAM MANAGER] Initialized")

#     def register_stream(self, sensor_id, stream):
#         self.datastreams[sensor_id] = stream
#         self.sensor_metadata[sensor_id] = {
#             "units": getattr(stream, "units", "unknown"),
#             "stream_type": getattr(stream, "stream_type", "unspecified"),
#             "sampling_interval_sec": getattr(stream, "interval", 1),
#         }

#         stream.start(interval=self.sensor_metadata[sensor_id]["sampling_interval_sec"])
#         print(f"[STREAM MANAGER] Registered and started stream: {stream.get_display_name()}")

#     def deregister_stream(self, sensor_id):
#         stream = self.datastreams.pop(sensor_id, None)
#         if stream:
#             stream.stop()
#             print(f"[STREAM MANAGER] Deregistered and stopped stream: {sensor_id}")

#     def _process_event(self, event, sender_alias):
#         sensor_id = event["sensor_id"]
#         alias = event.get("origin", sender_alias)  # fallback in case 'origin' missing
#         value = event["value"]
#         timestamp = event["timestamp"]
#         self.last_seen[sensor_id] = timestamp
#         meta = self.sensor_metadata.get(sensor_id, {})

#         print(f"[STREAM MANAGER] Received from {sensor_id}: {value} at timestamp {timestamp}")

#         if sensor_id not in self.filters:
#             print(f"[ERROR] No filter configured for sensor: {sensor_id}, please adjust config.")
#             return

#         kf = self.filters[sensor_id]
#         kf.predict()
#         kf.update(value)

#         confidence = compute_confidence(kf.get_covariance())
#         filtered_event = {
#             "origin_alias": alias,
#             "streamId": sensor_id,
#             "timestamp": timestamp,
#             "filteredMeasurement": kf.get_value(),
#             "quality": {
#                 "imputed": False,
#                 "confidence": confidence
#             },
#             "streamInfo": {
#                 "streamType": meta.get("stream_type", "unspecified"),
#                 "unit": meta.get("units", "unspecified"),
#                 "filterSource": kf.get_type()
#             }
#         }

#         validate_event(filtered_event)
#         topic = f"streammanager.{sender_alias}"
#         self.client.send_event(filtered_event, topic=topic)
#         print(f"[STREAM MANAGER] Published filtered event on topic '{topic}': {filtered_event}")

#     def handle_received_event(self, topic, event):
#         try:
#             if topic.endswith(".data"):
#                 sender_alias = topic.rsplit(".", 1)[0]
#                 self._process_event(event, sender_alias)
#         except Exception as e:
#             print(f"[STREAM MANAGER] Failed to process event from topic '{topic}': {e}")

#     def start(self):
#         print("[STREAM MANAGER] Running and listening for events...")
#         self.client.subscribe()

#     def stop(self):
#         for stream in self.datastreams.values():
#             stream.stop()
#         print("[STREAM MANAGER] All streams stopped.")
#         if self.client:
#             self.client.stop()
#             print("[STREAM MANAGER] Client connection closed.")

# def main():
#     stream_manager = StreamManager(config_path="config/config.json")
#     stream_thread = threading.Thread(target=stream_manager.start, daemon=True)
#     stream_thread.start()

#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("[MAIN] Shutting down StreamManager...")
#         stream_manager.stop()
#         stream_thread.join()
#         print("[MAIN] StreamManager fully exited.")

# if __name__ == "__main__":
#     main()

