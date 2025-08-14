from collections import deque
import logging
import time
from typing import Any, Dict, Union
from registry.RegisterTypes.FilterRegistry import FilterRegistry

class DataStream:
    def __init__(self, stream_id: str, metadata: dict, filter_entry: dict, filter_registry: FilterRegistry, history_len: int = 15):
        self.stream_id = stream_id
        self.metadata = self._extract_metadata(metadata)


        self.history = deque(maxlen=history_len) # base event 
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
            self.filter.predict()  # advance the internal state

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
    def refresh_metadata(self, new_metadata: dict, new_filter_entry: dict):
        updated_metadata = self._extract_metadata(new_metadata)
        if updated_metadata != self.metadata:
            logging.info(f"[DataStream:{self.stream_id}] Metadata updated.")
            self.metadata = updated_metadata
            self.refresh_filter(new_filter_entry, force_reinit=True)

    def refresh_filter(self, filter_entry: dict, force_reinit: bool = False):
        if not filter_entry:
            logging.warning(f"[DataStream:{self.stream_id}] No filter entry provided.")
            return

        new_type = filter_entry.get("type")
        if not new_type:
            logging.warning(f"[DataStream:{self.stream_id}] No filter type specified.")
            return

        new_constructor = self.filter_registry.get_constructor(new_type)
        new_params = self.filter_registry.get_params(new_type)

        if new_constructor is None:
            logging.error(f"[DataStream:{self.stream_id}] Constructor not found for filter type '{new_type}'.")
            return

        old_entry = self._last_filter_entry or {}
        needs_update = (
            force_reinit or
            old_entry.get("type") != new_type or
            old_entry.get("params") != new_params
        )

        if needs_update:
            logging.info(f"[DataStream:{self.stream_id}] Reinitializing filter due to change.")
            self.filter = new_constructor(**new_params)
            self._last_filter_entry = {
                "type": new_type,
                "params": new_params
            }

            # Replay history
            original_history = list(self.history)
            self.history.clear()
            self.processed_history.clear()

            for value in original_history:
                self.process_event(value)

            logging.debug(f"[DataStream:{self.stream_id}] Filter updated: {old_entry} → {self._last_filter_entry}")
