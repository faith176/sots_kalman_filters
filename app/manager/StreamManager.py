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
        self.client.subscribe_to("command")

        # Register handlers
        self.client.register_handler("data", self.handle_data)
        self.client.register_handler("command", self.handle_command)

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

    def deregister_filter_template(self, template_id):
        self.filter_templates.pop(template_id, None)
        logging.info(f"[StreamManager] Removed filter '{template_id}'")


    # -- Stream Registration --

    def register_stream(self, stream_id, metadata: dict):
        self.stream_metadata[stream_id] = metadata
        logging.info(f"[StreamManager] Registered new stream '{stream_id}'")
        if "filter_template" in metadata:
            self.assign_filter_to_stream(stream_id, metadata["filter_template"])

    def deregister_stream(self, stream_id):
        self.stream_metadata.pop(stream_id, None)
        self.unassign_filter_to_stream(stream_id)
        logging.info(f"[StreamManager] Removed stream '{stream_id}'")


    # -- Assigning Filter to Stream Registration --

    def assign_filter_to_stream(self, stream_id, template_id):
        if template_id not in self.filter_templates:
            logging.error(f"[StreamManager] Cannot assign unknown filter template '{template_id}'")
            return
        self.stream_filters[stream_id] = instantiate_filter(self.filter_templates[template_id])
        logging.info(f"[StreamManager] Assigned filter '{template_id}' to stream '{stream_id}'")

    def unassign_filter_to_stream(self, stream_id):
        if stream_id in self.stream_filters:
            del self.stream_filters[stream_id]
            logging.info(f"[StreamManager] Deregistered filter from stream '{stream_id}'")
        else:
            logging.warning(f"[StreamManager] No filter to remove for stream '{stream_id}'")

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

    def handle_command(self, topic, msg):
        logging.info(f"[StreamManager] Received command: {msg}")
        # TODO: Implement command logic

    def handle_config(self, topic, msg):
        logging.info(f"[StreamManager] Received config update: {msg}")
        # TODO: Handle live config updates


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
            logging.info("[StreamManager] Started")

    def stop(self):
        logging.info("[StreamManager] Stopping...")
        self.running = False
        if self.client:
            self.client.close()
        if self.thread:
            self.thread.join()
        logging.info("[StreamManager] Fully stopped.")


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
        logging.info("[MAIN] Shutting down StreamManager...")
        manager.stop()
        logging.info("[MAIN] StreamManager fully exited.")

if __name__ == "__main__":
    main()