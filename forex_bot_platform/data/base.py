"""Base data source class."""
from abc import ABC, abstractmethod


class DataSource(ABC):
    @abstractmethod
    def load(self, *args, **kwargs):
        """Load data and return a pandas.DataFrame"""
        raise NotImplementedError
