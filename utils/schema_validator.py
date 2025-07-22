import json
import jsonschema
from jsonschema import validate
import os

def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def validate_json(data, schema_path):
    schema = load_json(schema_path)
    jsonschema.validate(instance=data, schema=schema)
    return data

def validate_config(config_path):
    data = load_json(config_path)
    schema_path = os.path.join(os.path.dirname(__file__), "schemas", "config_schema.json")
    return validate_json(data, schema_path)

def validate_event(event_obj):
    schema_path = os.path.join(os.path.dirname(__file__), "schemas", "event_schema.json")
    return validate_json(event_obj, schema_path)
