import json
from typing import Any, Dict, Union
from filter.KalmanFilter import KalmanFilter2D, KalmanFilter3D

__author__ = "Feyi Adesanya"
__copyright__ = "Copyright 2025, Sustainable Systems and Methods Lab (SSM), McMaster University"
__license__ = "GPL-3.0"

"""
Utility helper functions
"""

def load_filter_templates(path: str) -> Dict[str, Dict[str, Any]]:
    """Load filter initalization params (filter template) from JSON file."""
    with open(path, "r") as f:
        return json.load(f)

def load_stream_metadata(path: str) -> Dict[str, Dict[str, Any]]:
    """Load stream metadata from JSON file."""
    with open(path) as f:
        return json.load(f)

def instantiate_filter(template: Dict[str, Any]) -> Union[KalmanFilter2D, KalmanFilter3D]:
    """Instantiate a filter object from a template."""
    ftype = template["type"]
    params = template["params"]
    if ftype == "2D":
        return KalmanFilter2D(**params)
    elif ftype == "3D":
        return KalmanFilter3D(**params)
    else:
        raise ValueError(f"Unknown filter type '{ftype}'")
