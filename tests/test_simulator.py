import pytest
from simulator.simulator import SimulatedSensorStream

def test_values_within_reasonable_bounds():
    stream = SimulatedSensorStream(amplitude=1.0, noise_std=0.1)
    for _ in range(20):
        value = stream.get_next_value()
        assert -2.0 <= value <= 2.0

def test_event_format():
    stream = SimulatedSensorStream(sensor_id="test-sensor")
    event = stream.get_next_event()
    assert "sensor_id" in event
    assert "timestamp" in event
    assert "value" in event
    assert isinstance(event["timestamp"], float)
    assert event["sensor_id"] == "test-sensor"
