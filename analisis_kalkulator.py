from abc import ABC, abstractmethod
from typing import List
from model import SpotifyTrack

class AnalyzerCalculator(ABC):
    @abstractmethod
    def calculate(self, data: List[SpotifyTrack]) -> dict:
        pass