from registry.Registry import Registry

class StreamRegistry(Registry):
    def validate(self, item_data: dict) -> bool:
        return "interval_sec" in item_data and "filter_template" in item_data

    def get_stream_type(self, stream_id: str):
        entry = self.get(stream_id)
        return entry.get("stream_type") if entry else None
