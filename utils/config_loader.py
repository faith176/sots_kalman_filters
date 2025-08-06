import json
from filter.KalmanFilter import KalmanFilter2D, KalmanFilter3D

def load_filter_templates(path):
    with open(path, "r") as f:
        return json.load(f) 


def instantiate_filter(template):
        ftype = template["type"]
        params = template["params"]
        if ftype == "2D":
            return KalmanFilter2D(**params)
        elif ftype == "3D":
            return KalmanFilter3D(**params)
        else:
            raise ValueError(f"Unknown filter type '{ftype}'")


def load_stream_metadata(path):
    with open(path) as f:
        return json.load(f)