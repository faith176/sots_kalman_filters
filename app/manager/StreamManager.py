import logging
import threading
import time

from datastream.Datastream import DataStream
from messaging.ClientTypes.StreamClient import StreamClient
from registry.RegisterTypes.FilterRegistry import FilterRegistry
from registry.RegisterTypes.StreamRegistry  import StreamRegistry

class StreamManager:
    def __init__(self, filter_config_path="config/filters.json", stream_config_path="config/streams.json"):
        self.client = StreamClient(name="StreamManager")
        self.running = False
        self.thread = None

        self.filter_registry = FilterRegistry(filter_config_path)
        self.stream_registry = StreamRegistry(stream_config_path)
        self.streams = {}

        # Setup messaging
        self.client.subscribe_to("data")
        self.client.subscribe_to("command.")
        self.client.register_handler("data", self.handle_data)
        self.client.register_handler("command", self.handle_command)

        # Initialize DataStreams
        self._initialize_streams()

    def _initialize_streams(self):
        for stream_id, metadata in self.stream_registry.get_all().items():
            template_id = metadata.get("filter_template")
            filter_entry = self.filter_registry.get(template_id) if template_id else None
            self.streams[stream_id] = DataStream(stream_id, metadata, filter_entry, self.filter_registry)
            logging.info(f"[StreamManager] Initialized stream '{stream_id}' with template '{template_id}'")

    # --- Filter Management ---
    def register_filter_template(self, template_id: str, filter_entry: dict):
        validation_result, errors = self.filter_registry.validate(filter_entry)
        if validation_result:
            self.filter_registry.update(template_id, filter_entry)
        else:
            logging.error(f"[StreamManager] Invalid filter template '{template_id}. \nErrors: {errors}'")

    def deregister_filter_template(self, template_id: str):
        self.filter_registry.remove(template_id)

    # --- Stream Management ---
    def register_stream(self, stream_id: str, metadata: dict):
        validation_result, errors = self.stream_registry.validate(metadata)
        if validation_result:
            self.stream_registry.update(stream_id, metadata)
            template_id = metadata.get("filter_template")
            filter_entry = self.filter_registry.get(template_id) if template_id else None
            self.streams[stream_id] = DataStream(stream_id, metadata, filter_entry, self.filter_registry)
        else:
            logging.error(f"[StreamManager] Invalid stream metadata for '{stream_id}. \nErrors: {errors}'")

    def deregister_stream(self, stream_id: str):
        self.stream_registry.remove(stream_id)
        self.streams.pop(stream_id, None)
        logging.info(f"[StreamManager] Deregistered stream '{stream_id}'")


    # ADD ASSIGN AND UNASSIGN FILTER FROM STREAM FUNCTIONS

    # --- Event Handlers ---
    def handle_data(self, topic, msg):
        logging.info(f"[StreamManager] Received data from {topic}: {msg}")
        stream_id = msg.get("stream_id")
        value = msg.get("value")
        if stream_id not in self.streams:
            logging.warning(f"[StreamManager] Unregistered stream '{stream_id}'")
            return

        result = self.streams[stream_id].process_event(value)
        self.client.send_event(result, topic=f"cep.{stream_id}")

    def handle_command(self, topic, msg):
        logging.info(f"[StreamManager] Received command: {msg}")
        # TODO


    def run(self):
        self.running = True
        logging.info("[StreamManager] Running...")
        try:
            self.client.join()
            self.client.subscribe()
        except Exception as e:
            logging.error(f"[StreamManager] Error: {e}")
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

# --- Main ---
def main():
    logging.basicConfig(level=logging.DEBUG)
    manager = StreamManager()
    manager.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop()

if __name__ == "__main__":
    main()
