import json
import logging
from abc import ABC, abstractmethod

class Registry(ABC):
    def __init__(self, registry_path: str):
        self.registry_path = registry_path
        self._registry = self._load_registry()

    def _load_registry(self):
        with open(self.registry_path, 'r') as f:
            return json.load(f)

    def save_registry(self):
        with open(self.registry_path, 'w') as f:
            json.dump(self._registry, f, indent=2)

    def get(self, item_id: str):
        return self._registry.get(item_id)

    def is_registered(self, item_id: str):
        return item_id in self._registry

    def get_all(self):
        return self._registry.copy()

    def update(self, item_id: str, new_data: dict):
        self._registry[item_id] = new_data
        self.save_registry()
        logging.info(f"[{self.__class__.__name__}] Updated '{item_id}'")

    def remove(self, item_id: str):
        if item_id in self._registry:
            del self._registry[item_id]
            self.save_registry()
            logging.info(f"[{self.__class__.__name__}] Removed '{item_id}'")

    @abstractmethod
    def validate(self, item_data: dict) -> bool:
        """
        Optionally enforce validation per subclass.
        """
        pass
