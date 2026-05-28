from abc import ABC, abstractmethod
from typing import List
from model import SpotifyTrack

class BaseAnalyzer(ABC):
    def __init__(self, data: List[SpotifyTrack]):
        self._data = data 

    @abstractmethod
    def analyze(self) -> dict:
        pass

    @abstractmethod
    def display(self) -> None:
        pass

    def get_total(self) -> int:
        return len(self._data)