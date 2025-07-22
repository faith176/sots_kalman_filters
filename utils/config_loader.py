import os
from utils.schema_validator import validate_config
from filter.kalman_filter import KalmanFilter2D, KalmanFilter3D

def load_filters_from_config(config_path):
    config = validate_config(config_path)
    sensor_configs = config["sensors"]

    filters = {}
    for sensor in sensor_configs:
        fcfg = sensor["filter"]
        if fcfg["type"] == "2D":
            filters[sensor["sensor_id"]] = KalmanFilter2D(
                fcfg["initial_value"],
                fcfg["initial_rate"],
                fcfg["initial_variance"],
                fcfg["dt"],
                fcfg["process_noise"],
                fcfg["measurement_noise"]
            )
        elif fcfg["type"] == "3D":
            filters[sensor["sensor_id"]] = KalmanFilter3D(
                fcfg["initial_value"],
                fcfg["initial_rate"],
                fcfg["initial_acceleration"],
                fcfg["initial_variance"],
                fcfg["dt"],
                fcfg["process_noise"],
                fcfg["measurement_noise"]
            )
    return filters
