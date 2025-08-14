from registry.Registry import Registry

class StreamRegistry(Registry):
    def validate(self, item_data: dict) -> bool:
        return "interval_sec" in item_data and "filter_template" in item_data

    def get_stream_type(self, stream_id: str):
        entry = self.get(stream_id)
        return entry.get("stream_type") if entry else None
    

    def validate(self, item_data: dict) -> bool:
        errors = []

        if not isinstance(item_data, dict):
            errors.append("Item is not an object/dict.")
            return False, errors

        required = {"stream_type", "unit", "datatype", "interval_sec", "filter_template"}
        for key in sorted(required):
            if key not in item_data:
                errors.append(f"Missing required key: '{key}'.")

        if errors:
            return False, errors

        # stream_type
        if not isinstance(item_data["stream_type"], str) or not item_data["stream_type"]:
            errors.append("Field 'stream_type' must be a non-empty string.")

        # unit
        if not isinstance(item_data["unit"], str) or not item_data["unit"]:
            errors.append("Field 'unit' must be a non-empty string.")

        # datatype
        allowed_types = {"float", "int", "bool", "string"}
        dt = item_data["datatype"]
        if dt not in allowed_types:
            errors.append(f"Field 'datatype' must be one of {sorted(allowed_types)}.")

        # interval_sec
        iv = item_data["interval_sec"]
        if not self._is_int(iv) or iv <= 0:
            errors.append("Field 'interval_sec' must be a positive integer.")

        # filter_template
        ft = item_data["filter_template"]
        if not isinstance(ft, str) or not ft:
            errors.append("Field 'filter_template' must be a non-empty string.")

        return len(errors) == 0, errors


