import json
import zmq
class ZMQPublisher:
    def __init__(self, endpoint="tcp://*:5556"):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.address = endpoint
        self.socket.bind(self.address)

    def publish(self, topic: str, data: dict):
        message = json.dumps(data)
        self.socket.send_string(f"{topic} {message}")

    def close(self):
        self.socket.close()
        self.context.term()


class ZMQSubscriber:
    def __init__(self, endpoint="tcp://localhost:5556", topic_filter=""):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(endpoint)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, topic_filter)

    def receive(self):
        topic, message = self.socket.recv_string().split(" ", 1)
        data = json.loads(message)
        return topic, data

    def close(self):
        self.socket.close()
        self.context.term()
