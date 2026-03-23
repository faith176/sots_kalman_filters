import json
from ..schema.Event import Event

__author__ = "Feyi Adesanya"

"""
General utility functions.
"""

def _load_json(path: str) -> dict:
        with open(path, "r") as f:
            return json.load(f)
        
def _serialize_event(event: Event) -> bytes:
    return json.dumps(event).encode("utf-8")

def _deserialize_event(data: bytes) -> Event:
    return json.loads(data.decode("utf-8"))

# for the statecharts
def _as_observer(fn):
        class _Observer:
            def next(self, value=None):
                if value is not None:
                    fn(value)
                else:
                    fn()
        return _Observer()