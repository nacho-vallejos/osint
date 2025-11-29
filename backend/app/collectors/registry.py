from typing import Dict, Type
from app.collectors.base import BaseCollector

class CollectorRegistry:
    def __init__(self):
        self._collectors: Dict[str, Type[BaseCollector]] = {}
    
    def register(self, collector_class: Type[BaseCollector]) -> None:
        self._collectors[collector_class.__name__] = collector_class
    
    def get_collector(self, name: str) -> BaseCollector:
        collector_class = self._collectors.get(name)
        if not collector_class:
            raise ValueError(f"Collector '{name}' not found")
        return collector_class()
    
    def list_collectors(self) -> list:
        return list(self._collectors.keys())

registry = CollectorRegistry()
