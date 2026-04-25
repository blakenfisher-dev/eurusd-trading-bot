"""Base strategy class."""
from typing import Dict, Any

class Strategy:
    name: str
    params: Dict[str, Any]

    def __init__(self, name: str, **params):
        self.name = name
        self.params = params

    def generate_signal(self, data) -> int:
        """Return a simple signal: 1 for long, -1 for short, 0 for hold."""
        return 0
