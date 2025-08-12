import json
import pytest

from utils.config_loader import load_filter_templates, load_stream_metadata, instantiate_filter
from filter.KalmanFilter import KalmanFilter2D, KalmanFilter3D


def test_load_filter_templates(tmp_path):
    data = {
        "kf1": {
            "type": "2D",
            "params": {
                "initial_value": 10.0,
                "initial_rate": 0.0,
                "initial_variance": 1.0,
                "dt": 1.0,
                "process_noise": 0.01,
                "measurement_noise": 0.1,
            },
        }
    }
    fpath = tmp_path / "filters.json"
    fpath.write_text(json.dumps(data))

    loaded = load_filter_templates(str(fpath))
    assert loaded == data
    assert "kf1" in loaded
    assert loaded["kf1"]["type"] == "2D"


def test_load_stream_metadata(tmp_path):
    data = {
        "temp-sensor-001": {
            "stream_type": "temperature",
            "units": "°C",
            "filter_template": "kf1",
            "sampling_interval": 1.0,
        }
    }
    fpath = tmp_path / "streams.json"
    fpath.write_text(json.dumps(data))

    loaded = load_stream_metadata(str(fpath))
    assert loaded == data
    assert "temp-sensor-001" in loaded
    assert loaded["temp-sensor-001"]["units"] == "°C"


def test_instantiate_filter_2d():
    template = {
        "type": "2D",
        "params": {
            "initial_value": 20.0,
            "initial_rate": 0.1,
            "initial_variance": 2.0,
            "dt": 0.5,
            "process_noise": 0.02,
            "measurement_noise": 0.15,
        },
    }
    kf = instantiate_filter(template)
    assert isinstance(kf, KalmanFilter2D)
    # Sanity checks based on your implementation
    assert kf.get_type() == "2D"
    assert pytest.approx(kf.get_value(), rel=1e-9) == 20.0


def test_instantiate_filter_3d():
    template = {
        "type": "3D",
        "params": {
            "initial_value": 5.0,
            "initial_rate": 0.0,
            "initial_acceleration": 0.0,
            "initial_variance": 1.5,
            "dt": 1.0,
            "process_noise": 0.05,
            "measurement_noise": 0.2,
        },
    }
    kf = instantiate_filter(template)
    assert isinstance(kf, KalmanFilter3D)
    assert kf.get_type() == "3D"
    assert pytest.approx(kf.get_value(), rel=1e-9) == 5.0


def test_instantiate_filter_unknown_type_raises():
    template = {"type": "ABC", "params": {}}
    with pytest.raises(ValueError) as excinfo:
        instantiate_filter(template)
    assert "Unknown filter type" in str(excinfo.value)


def test_instantiate_filter_missing_keys_raises():
    # Missing "params"
    template_missing_params = {"type": "2D"}
    with pytest.raises(KeyError):
        instantiate_filter(template_missing_params)

    # Missing "type"
    template_missing_type = {"params": {"initial_value": 1.0}}
    with pytest.raises(KeyError):
        instantiate_filter(template_missing_type)
