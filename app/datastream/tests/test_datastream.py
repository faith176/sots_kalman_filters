import time
from collections import deque

import pytest

class DummyFilter:
    """
    Super-simple filter:
    - state starts at initial (default 0.0).
    - predict(): state += 1.0 (just to be clearly visible in tests)
    - update(z): state = z; returns (estimate, confidence, std_dev)
    - get_prediction(): returns (state, 0.5, 0.0)
    """
    def __init__(self, initial=0.0):
        self.state = float(initial)
        self.P = None  # not used by DataStream, but could exist

    def predict(self):
        self.state += 1.0

    def update(self, measurement):
        self.state = float(measurement)
        return (self.state, 1.0, 0.0) # unpack for real measurement

    def get_prediction(self):
        return (self.state, 0.5, 0.0)

class DummyFilterV2(DummyFilter):
    """A variant so we can assert that refresh swaps constructors."""
    def predict(self):
        # different predict behavior (+= 2) to distinguish different after filter refresh activates
        self.state += 2.0

class FakeFilterRegistry:
    def __init__(self):
        self._constructors = {
            "Dummy2D": lambda **kw: DummyFilter(**kw),
            "Dummy3D": lambda **kw: DummyFilterV2(**kw),
        }
        self._params = {
            "Dummy2D": {"initial": 0.0},
            "Dummy3D": {"initial": 10.0},
        }

    def get_constructor(self, filter_type):
        return self._constructors.get(filter_type)

    def get_params(self, filter_type):
        return dict(self._params.get(filter_type, {}))


# ---- System under test -------------------------------------------------------
from datastream.Datastream import DataStream


# ---- Tests -------------------------------------------------------------------

def test_process_event_with_measurement_no_imputation(monkeypatch):
    registry = FakeFilterRegistry()
    metadata = {
        "name": "temp-sensor-001",
        "stream_type": "temperature",
        "unit": "Celsius",
        "datatype": "float",
        "interval_sec": 2,
        "filter_template": "Dummy2D",
    }
    filter_entry = {"type": "Dummy2D"}

    ds = DataStream(
        stream_id="temp-sensor-001",
        metadata=metadata,
        filter_entry=filter_entry,
        filter_registry=registry,
        history_len=5,
    )

    # 1) process with a measurement
    out = ds.process_event(42.0)

    assert out["stream_id"] == "temp-sensor-001"
    assert out["value"] == 42.0
    assert out["unit"] == "Celsius"
    assert out["datatype"] == "float"
    assert out["imputation"]["flag"] is False
    assert out["imputation"]["confidence"] == 1.0


def test_process_event_missing_value_imputation_path():
    registry = FakeFilterRegistry()
    metadata = {
        "name": "temp-sensor-001",
        "stream_type": "temperature",
        "unit": "Celsius",
        "datatype": "float",
        "interval_sec": 2,
        "filter_template": "Dummy2D",
    }
    ds = DataStream(
        stream_id="temp-sensor-001",
        metadata=metadata,
        filter_entry={"type": "Dummy2D"},
        filter_registry=registry,
        history_len=5,
    )

    # Feed a real value to advance state, then a missing measurement to move to the imputation path
    ds.process_event(10.0)
    out = ds.process_event(None)

    assert out["imputation"]["flag"] is True
    assert out["imputation"]["estimate"] == pytest.approx(11.0) # Dummy2D predict += 1.0, so next predict should be 10+1 = 11
    assert out["imputation"]["confidence"] == pytest.approx(0.5)
    assert out["imputation"]["std_dev"] == pytest.approx(0.0)


def test_refresh_filter_replays_history_and_swaps_constructor():
    registry = FakeFilterRegistry()
    metadata = {
        "name": "temp-sensor-001",
        "stream_type": "temperature",
        "unit": "Celsius",
        "datatype": "float",
        "interval_sec": 1,
        "filter_template": "Dummy2D",
    }
    ds = DataStream(
        stream_id="temp-sensor-001",
        metadata=metadata,
        filter_entry={"type": "Dummy2D"},
        filter_registry=registry,
        history_len=10,
    )

    out1 = ds.process_event(1.0)
    out2 = ds.process_event(None)
    out3 = ds.process_event(2.0)
    original_history = list(ds.history)
    assert original_history == [1.0, None, 2.0]
    assert len(ds.processed_history) == 3

    # Refresh to a different type (Dummy3D)
    ds.refresh_filter("Dummy3D", force_reinit=True)

    # After refresh, history should have been replayed
    assert list(ds.history) == original_history
    assert len(ds.processed_history) == 3

    # Ensure the last output reflects the new constructor behavior.
    # With Dummy3D initial=10.0:
    #   Replay 1) value=1.0: predict first (10->12), update to 1.0, confidence=1.0
    #   Replay 2) value=None: predict (1.0->3.0), impute estimate=3.0
    #   Replay 3) value=2.0: predict (3.0->5.0), update to 2.0
    last = ds.get_latest()
    assert last["imputation"]["estimate"] == pytest.approx(2.0)
    assert last["imputation"]["confidence"] == 1.0
    assert last["imputation"]["flag"] is False
    assert last["imputation"]["method"] == "Dummy3D" # Verify the recorded "method" matches the new filter type


def test_no_filter_entry_results_in_none_estimates():
    registry = FakeFilterRegistry()
    metadata = {
        "name": "no-filter-stream",
        "stream_type": "generic",
        "unit": "",
        "datatype": "float",
        "interval_sec": 1,
        "filter_template": None,
    }
    ds = DataStream(
        stream_id="no-filter",
        metadata=metadata,
        filter_entry=None,  # no filter provided
        filter_registry=registry,
        history_len=3,
    )

    out = ds.process_event(5.0)

    assert out["imputation"]["method"] is None
    assert out["imputation"]["estimate"] is None
    assert out["imputation"]["confidence"] is None
    assert out["imputation"]["std_dev"] is None
    assert out["imputation"]["flag"] is False




def test_refresh_metadata_does_not_reinit_when_template_unchanged():
    registry = FakeFilterRegistry()
    meta_v1 = {
        "name": "temp-sensor-001",
        "stream_type": "temperature",
        "unit": "C",
        "datatype": "float",
        "interval_sec": 1,
        "filter_template": "Dummy2D",
    }
    ds = DataStream(
        stream_id="temp-sensor-001",
        metadata=meta_v1,
        filter_entry={"type": "Dummy2D"},
        filter_registry=registry,
        history_len=10,
    )

    # Prime with some values
    ds.process_event(0.0)
    ds.process_event(None)

    old_seq = ds.get_latest()["sequence"]
    old_filter_obj = ds.filter
    old_history = list(ds.history)
    old_processed_len = len(ds.processed_history)

    # Change metadata but keep same filter template
    meta_v2 = dict(meta_v1)
    meta_v2["interval_sec"] = 2  # triggers metadata update only

    # Even with force_reinit=True, template is unchanged so no replay and no swap
    ds.refresh_metadata(new_metadata=meta_v2, force_reinit=True)

    # Metadata updated
    assert ds.metadata["interval"] == 2
    assert ds.filter is old_filter_obj
    assert list(ds.history) == old_history
    assert len(ds.processed_history) == old_processed_len
    assert ds.get_latest()["sequence"] == old_seq


def test_refresh_metadata_swaps_filter_and_replays_when_template_changes_and_forced():
    registry = FakeFilterRegistry()
    meta_v1 = {
        "name": "temp-sensor-001",
        "stream_type": "temperature",
        "unit": "C",
        "datatype": "float",
        "interval_sec": 1,
        "filter_template": "Dummy2D",
    }
    ds = DataStream(
        stream_id="temp-sensor-001",
        metadata=meta_v1,
        filter_entry={"type": "Dummy2D"},
        filter_registry=registry,
        history_len=10,
    )

    ds.process_event(1.0)
    ds.process_event(None)

    old_seq = ds.get_latest()["sequence"]

    # Change filter to a different one
    meta_v2 = dict(meta_v1)
    meta_v2["filter_template"] = "Dummy3D"

    ds.refresh_metadata(new_metadata=meta_v2, force_reinit=True)

    assert ds.metadata["filter_template"] == "Dummy3D"
    assert list(ds.history) == [1.0, None]
    assert len(ds.processed_history) == 2
    assert ds.get_latest()["sequence"] > old_seq


def test_refresh_metadata_swaps_filter_and_resets_when_template_changes_no_replay():
    registry = FakeFilterRegistry()
    meta_v1 = {
        "name": "s1",
        "stream_type": "temperature",
        "unit": "C",
        "datatype": "float",
        "interval_sec": 1,
        "filter_template": "Dummy2D",
    }
    ds = DataStream(
        stream_id="s1",
        metadata=meta_v1,
        filter_entry={"type": "Dummy2D"},
        filter_registry=registry,
        history_len=10,
    )

    ds.process_event(5.0)
    ds.process_event(None)

    # Change template but do not replay
    meta_v2 = dict(meta_v1)
    meta_v2["filter_template"] = "Dummy3D"

    ds.refresh_metadata(new_metadata=meta_v2, force_reinit=False)

    # Template updated; histories cleared (reset mode)
    assert ds.metadata["filter_template"] == "Dummy3D"
    assert list(ds.history) == []
    assert len(ds.processed_history) == 0
