from collections import deque
import logging
import time
from typing import Any, Dict, Union
from registry.RegisterTypes.FilterRegistry import FilterRegistry

class DataStream:
    def __init__(self, stream_id: str, metadata: dict, filter_entry: dict, filter_registry: FilterRegistry, history_len: int = 15):
        self.stream_id = stream_id
        self.metadata = self._extract_metadata(metadata)

        self.history = deque(maxlen=history_len) # values 
        self.processed_history = deque(maxlen=history_len) # formatted event
        self._sequence_counter = 0

        self.filter_registry = filter_registry
        self._last_filter_entry = filter_entry
        self.filter = self._init_filter(filter_entry)

    # Kalman Filter Steps
    def process_event(self, value) -> Dict[str, Any]:
        self.history.append(value)
        
        # Predict first
        estimate, confidence, std_dev = None, None, None
        if self.filter:
            self.filter.predict()

        has_measurement = value is not None

        # Apply update only if value is present
        if self.filter:
            if has_measurement:
                estimate, confidence, std_dev = self.filter.update(value)
                imputed = False
                confidence = 1.0
            else:
                # Use predicted state without update
                estimate, confidence, std_dev = self.filter.get_prediction()
                imputed = True
        else:
            estimate, confidence, std_dev = None, None, None
            imputed = False

        # Format and store
        output = self._format_event(value, imputed, (estimate, confidence, std_dev))
        self.processed_history.append(output)
        logging.debug(f"[DataStream:{self.stream_id}] Processed value: {value}, Imputed: {imputed}")
        return output


    def _format_event(self, value, imputed, filter_output: tuple) -> dict:
        self._sequence_counter += 1
        timestamp = time.time()
        estimate, confidence, std_dev = filter_output if filter_output else (None, None, None)

        return {
            "stream_id": self.stream_id,
            "sequence": self._sequence_counter,
            "timestamp": timestamp,
            "value": value,
            "unit": self.metadata["unit"],
            "datatype": self.metadata["datatype"],
            "interval": self.metadata["interval"],
            "location": self.metadata["location"],
            "validity_range": self.metadata["validity_range"],
            "imputation": {
                "flag": imputed,
                "method": self.metadata["filter_template"],
                "estimate": estimate,
                "confidence": confidence,
                "std_dev": std_dev,
            }
        }
    
    def get_latest(self) -> dict:
        return self.processed_history[-1] if self.processed_history else None

    def _extract_metadata(self, config: dict) -> dict:
        return {
            "name": config.get("name", self.stream_id),
            "stream_type": config.get("stream_type", "generic"),
            "unit": config.get("unit", ""),
            "interval": config.get("interval_sec", 1.0),
            "filter_template": config.get("filter_template", None),
            "datatype": config.get("datatype", "float"),
            "location": config.get("location", None),
            "validity_range": config.get("validity_range", None),
        }
    
    def _init_filter(self, filter_entry: dict):
        if not filter_entry:
            return None

        filter_name = filter_entry.get("type")
        if not filter_name:
            logging.warning(f"[DataStream:{self.stream_id}] No filter type provided.")
            return None

        constructor = self.filter_registry.get_constructor(filter_name)
        params = self.filter_registry.get_params(filter_name)

        if constructor is None:
            logging.error(f"[DataStream:{self.stream_id}] Filter class for '{filter_name}' not found.")
            return None

        self._last_filter_entry = {
            "type": filter_name,
            "params": params
        }

        return constructor(**params)



    # Refresh Logic
    def refresh_metadata(self, new_metadata: dict, force_reinit: bool = False) -> None:
        updated = self._extract_metadata(new_metadata)

        if updated == self.metadata:
            logging.debug(f"[DataStream:{self.stream_id}] Metadata unchanged")
            return

        old_template = self.metadata.get("filter_template")
        new_template = updated.get("filter_template")

        # Apply all non-filter metadata immediately
        self.metadata = updated
        logging.info(f"[DataStream:{self.stream_id}] Metadata updated.")

        # If template is unchanged, nothing else to do
        if new_template == old_template:
            return

        # Try to swap filter; on failure, revert template name to reflect reality
        if not self.refresh_filter(new_template, force_reinit=force_reinit):
            logging.error(
                f"[DataStream:{self.stream_id}] Could not apply filter_template '{new_template}'; "
                f"keeping existing filter '{old_template}'."
            )
            self.metadata["filter_template"] = old_template
        print(self.metadata)
        print(self.processed_history)


    def refresh_filter(self, filter_type: str, force_reinit: bool = False) -> bool:
        new_type = filter_type.strip()
        new_constructor = self.filter_registry.get_constructor(new_type)
        if new_constructor is None:
            logging.error(f"[DataStream:{self.stream_id}] Constructor not found for filter type '{new_type}'.")
            return False

        new_params = self.filter_registry.get_params(new_type)
        old_entry = self._last_filter_entry or {}
        old_type = old_entry.get("type")

        # snapshot only if replaying
        original_history = list(self.history) if force_reinit else None

        try:
            self.filter = new_constructor(**new_params)
        except Exception as e:
            logging.exception(f"[DataStream:{self.stream_id}] Failed to initialize filter '{new_type}': {e}")
            if old_type:
                self.metadata["filter_template"] = old_type
            return False

        self._last_filter_entry = {"type": new_type, "params": new_params}
        self.metadata["filter_template"] = new_type

        self.history.clear()
        self.processed_history.clear()

        if force_reinit and original_history is not None:
            logging.info(f"[DataStream:{self.stream_id}] Reinitializing filter and REPLAYING history.")
            for value in original_history:
                self.process_event(value)
        else:
            logging.info(f"[DataStream:{self.stream_id}] Reinitializing filter and RESETTING history (no replay).")

        logging.debug(
            f"[DataStream:{self.stream_id}] Filter updated: {old_type} → {new_type}; "
            f"force_reinit={force_reinit}"
        )
        return True
