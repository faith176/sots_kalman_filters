import logging
from filter.KalmanFilter import KalmanFilter2D, KalmanFilter3D
from registry.Registry import Registry

FILTER_TYPE_MAP = {
    "KalmanFilter2D": KalmanFilter2D,
    "KalmanFilter3D": KalmanFilter3D,
}

class FilterRegistry(Registry):
    def get_constructor(self, filter_name: str):
        entry = self.get(filter_name)
        if not entry:
            logging.warning(f"[FilterRegistry] No filter entry found for '{filter_name}'")
            return None
        return FILTER_TYPE_MAP.get(entry["class"])

    def get_params(self, filter_name: str):
        entry = self.get(filter_name)
        if not entry:
            logging.warning(f"[FilterRegistry] No filter entry found for '{filter_name}'")
            return {}
        return entry.get("params")
    
    def validate(self, item_data: dict) -> bool:
        errors = []

        if not isinstance(item_data, dict):
            errors.append("Item is not an object/dict.")
            return False, errors

        # Required
        for key in ("type", "params"):
            if key not in item_data:
                errors.append(f"Missing required top-level key: '{key}'.")

        if errors:
            return False, errors

        # type
        kf_type = item_data["type"]
        if kf_type not in {"KalmanFilter2D", "KalmanFilter3D"}:
            errors.append("Field type not defined")

        # params
        params = item_data["params"]
        if not isinstance(params, dict):
            errors.append("Field params must be an object/dict.")
            return False, errors

        # Required params
        base_required = {
            "initial_value",
            "initial_rate",
            "initial_variance",
            "dt",
            "process_noise",
            "measurement_noise",
        }
        required = set(base_required)
        if kf_type == "KalmanFilter3D":
            required.add("initial_acceleration")

        for req in sorted(required):
            if req not in params:
                errors.append(f"Missing required param: '{req}'.")

        return len(errors) == 0, errors
