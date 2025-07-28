from utils.schema_validator import validate_config
from filter.kalman_filter import KalmanFilter2D, KalmanFilter3D

def load_filters_from_config(config_path):
    config = validate_config(config_path)
    sensor_configs = config["sensors"]

    filters = {}
    for sensor in sensor_configs:
        sample = sensor["filter"]
        if sample["type"] == "2D":
            filters[sensor["sensor_id"]] = KalmanFilter2D(
                sample["initial_value"],
                sample["initial_rate"],
                sample["initial_variance"],
                sample["dt"],
                sample["process_noise"],
                sample["measurement_noise"]
            )
        elif sample["type"] == "3D":
            filters[sensor["sensor_id"]] = KalmanFilter3D(
                sample["initial_value"],
                sample["initial_rate"],
                sample["initial_acceleration"],
                sample["initial_variance"],
                sample["dt"],
                sample["process_noise"],
                sample["measurement_noise"]
            )
    return filters
