import time
import threading
import pytest
from publish.zmq_setup import ZMQPublisher, ZMQSubscriber

@pytest.fixture
def zmq_setup():
    endpoint_pub = "tcp://*:5557"
    endpoint_sub = "tcp://localhost:5557"

    publisher = ZMQPublisher(endpoint=endpoint_pub)
    subscriber = ZMQSubscriber(endpoint=endpoint_sub)
    time.sleep(0.1)  # Allow ZMQ sockets to connect

    yield publisher, subscriber

    publisher.close()
    subscriber.close()

def test_pub_sub_cycle(zmq_setup):
    publisher, subscriber = zmq_setup

    def send_message():
        time.sleep(0.1)
        publisher.publish("sensor1", {"test": 123})

    sender_thread = threading.Thread(target=send_message)
    sender_thread.start()

    topic, message = subscriber.receive()
    assert topic == "sensor1"
    assert message["test"] == 123
