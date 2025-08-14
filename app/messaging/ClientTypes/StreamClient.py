import json
import logging
import zmq

from messaging.Client import Client

class StreamClient(Client):
    def __init__(self, name="default-stream"):
        super().__init__()
        self.name = name
        self.subscriptions = set()
        self.handlers = {}

    def send_event(self, event: dict, topic: str = None):
        topic = topic or f"data.{self.name}"
        self._publisher.send_multipart([topic.encode(), json.dumps(event).encode()])
        logging.debug(f"[StreamClient:{self.name}] Sent on topic '{topic}': {event}")

    def subscribe_to(self, topic: str):
        self._subscriber.setsockopt_string(zmq.SUBSCRIBE, topic)
        self.subscriptions.add(topic)
        logging.info(f"[StreamClient:{self.name}] Subscribed to '{topic}'")

    def unsubscribe_from(self, topic: str):
        self._subscriber.setsockopt_string(zmq.UNSUBSCRIBE, topic)
        self.subscriptions.discard(topic)
        logging.info(f"[StreamClient:{self.name}] Unsubscribed from '{topic}'")

    def register_handler(self, prefix: str, handler_fn):
        if prefix in self.handlers:
            logging.warning(f"[StreamClient:{self.name}] Overwriting handler for prefix '{prefix}'")
        self.handlers[prefix] = handler_fn
        logging.info(f"[StreamClient:{self.name}] Registered handler for '{prefix}.*'")

    def deregister_handler(self, prefix: str):
        if prefix in self.handlers:
            del self.handlers[prefix]
            logging.info(f"[StreamClient:{self.name}] Deregistered handler for prefix '{prefix}'")
        else:
            logging.warning(f"[StreamClient:{self.name}] No handler registered for prefix '{prefix}'")


    def subscriberAction(self):
        try:
            parts = self._subscriber.recv_multipart(zmq.NOBLOCK)
            if len(parts) < 2:
                logging.warning(f"[StreamClient:{self.name}] Malformed message: {parts}")
                return

            topic = parts[0].decode()
            payload = parts[1].decode()

            try:
                event = json.loads(payload)
            except json.JSONDecodeError as e:
                logging.error(f"[StreamClient:{self.name}] JSON error: {e}")
                return

            try:
                prefix = topic.split(".", 1)[0] # e.g., 'data', 'command'
            except IndexError:
                logging.error(f"[StreamClient:{self.name}] Invalid topic format: '{topic}'")
                return


            if prefix in self.handlers:
                self.handlers[prefix](topic, event)
            else:
                logging.warning(f"[StreamClient:{self.name}] No handler for prefix '{prefix}'")

        except zmq.Again:
            pass
        except Exception as e:
            logging.error(f"[StreamClient:{self.name}] Error in subscriberAction: {e}")

    def timeoutAction(self):
        pass

    def close(self):
        self._subscriber.close()
        self._publisher.close()
        logging.info(f"[StreamClient:{self.name}] Closed sockets.")

