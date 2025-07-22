import tempfile
import json
import os
import pytest
from filter.kalman_filter import KalmanFilter2D, KalmanFilter3D
from utils.config_loader import load_filters_from_config
from jsonschema.exceptions import ValidationError

@pytest.fixture
def temp_config_env(monkeypatch):
    temp_dir = tempfile.TemporaryDirectory()
    config_path = os.path.join(temp_dir.name, "config.json")
    schema_dir = os.path.join(temp_dir.name, "schemas")
    os.makedirs(schema_dir, exist_ok=True)

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "sensors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["sensor_id", "filter"],
                    "properties": {
                        "sensor_id": {"type": "string"},
                        "filter": {
                            "type": "object",
                            "required": ["type"],
                            "properties": {
                                "type": {"type": "string", "enum": ["2D", "3D"]}
                            }
                        }
                    }
                }
            }
        },
        "required": ["sensors"]
    }

    with open(os.path.join(schema_dir, "config_schema.json"), "w") as f:
        json.dump(schema, f)

    monkeypatch.setattr(os.path, "dirname", lambda _: temp_dir.name)

    yield temp_dir.name, config_path

    temp_dir.cleanup()


def test_load_2d_filter(temp_config_env):
    temp_dir, config_path = temp_config_env
    config = {
        "sensors": [
            {
                "sensor_id": "sensor-1",
                "filter": {
                    "type": "2D",
                    "initial_value": 0.0,
                    "initial_rate": 0.0,
                    "initial_variance": 1.0,
                    "dt": 1.0,
                    "process_noise": 0.1,
                    "measurement_noise": 0.5
                }
            }
        ]
    }

    with open(config_path, "w") as f:
        json.dump(config, f)

    filters = load_filters_from_config(config_path)
    assert "sensor-1" in filters
    assert isinstance(filters["sensor-1"], KalmanFilter2D)


def test_load_3d_filter(temp_config_env):
    temp_dir, config_path = temp_config_env
    config = {
        "sensors": [
            {
                "sensor_id": "sensor-2",
                "filter": {
                    "type": "3D",
                    "initial_value": 1.0,
                    "initial_rate": 0.5,
                    "initial_acceleration": 0.2,
                    "initial_variance": 1.0,
                    "dt": 1.0,
                    "process_noise": 0.01,
                    "measurement_noise": 0.1
                }
            }
        ]
    }

    with open(config_path, "w") as f:
        json.dump(config, f)

    filters = load_filters_from_config(config_path)
    assert "sensor-2" in filters
    assert isinstance(filters["sensor-2"], KalmanFilter3D)


def test_invalid_filter_type(temp_config_env):
    temp_dir, config_path = temp_config_env
    config = {
        "sensors": [
            {
                "sensor_id": "sensor-x",
                "filter": {
                    "type": "1D"
                }
            }
        ]
    }

    with open(config_path, "w") as f:
        json.dump(config, f)

    with pytest.raises(ValidationError):
        load_filters_from_config(config_path)
