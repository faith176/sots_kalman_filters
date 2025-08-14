import logging
from filter.KalmanFilter import KalmanFilter2D, KalmanFilter3D
from registry.Registry import Registry

FILTER_TYPE_MAP = {
    "KalmanFilter2D": KalmanFilter2D,
    "KalmanFilter3D": KalmanFilter3D,
}

class FilterRegistry(Registry):
    def validate(self, item_data: dict) -> bool:
        return "class" in item_data and "params" in item_data

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
