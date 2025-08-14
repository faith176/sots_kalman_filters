import json
import os
import pytest
from tempfile import NamedTemporaryFile

from registry.RegisterTypes.FilterRegistry import FilterRegistry
from registry.RegisterTypes.StreamRegistry import StreamRegistry



@pytest.fixture
def temp_filter_registry_file():
    data = {
        "kf_2d": {
            "class": "KalmanFilter2D",
            "params": {"initial_value": 0.0, "initial_rate": 0.0}
        }
    }
    with NamedTemporaryFile(mode='w+', delete=False, suffix=".json") as tmp:
        json.dump(data, tmp)
        tmp.flush()
        yield tmp.name
    os.remove(tmp.name)

@pytest.fixture
def temp_stream_registry_file():
    data = {
        "stream1": {
            "stream_type": "temperature",
            "interval_sec": 5,
            "filter_template": "kf_2d"
        }
    }
    with NamedTemporaryFile(mode='w+', delete=False, suffix=".json") as tmp:
        json.dump(data, tmp)
        tmp.flush()
        yield tmp.name
    os.remove(tmp.name)


def test_filter_registry_load(temp_filter_registry_file):
    registry = FilterRegistry(temp_filter_registry_file)
    assert registry.is_registered("kf_2d")
    assert registry.get("kf_2d")["class"] == "KalmanFilter2D"


def test_filter_registry_get_constructor_and_params(temp_filter_registry_file):
    registry = FilterRegistry(temp_filter_registry_file)
    constructor = registry.get_constructor("kf_2d")
    params = registry.get_params("kf_2d")
    assert constructor is not None
    assert isinstance(params, dict)
    assert "initial_value" in params

def test_stream_registry_load(temp_stream_registry_file):
    registry = StreamRegistry(temp_stream_registry_file)
    assert registry.is_registered("stream1")
    stream = registry.get("stream1")
    assert stream["stream_type"] == "temperature"

def test_stream_registry_get_stream_type(temp_stream_registry_file):
    registry = StreamRegistry(temp_stream_registry_file)
    assert registry.get_stream_type("stream1") == "temperature"
    assert registry.get_stream_type("nonexistent") is None

