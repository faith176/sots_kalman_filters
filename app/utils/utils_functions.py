import json
from typing import Any, Dict, Union
from filter.KalmanFilter import KalmanFilter2D, KalmanFilter3D

__author__ = "Feyi Adesanya"
__copyright__ = "Copyright 2025, Sustainable Systems and Methods Lab (SSM), McMaster University"
__license__ = "GPL-3.0"

"""
Utility helper functions
"""

def load_config(path: str) -> Dict[str, Dict[str, Any]]:
    """Load config information from JSON file."""
    with open(path, "r") as f:
        return json.load(f)
