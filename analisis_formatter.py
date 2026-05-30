from abc import ABC, abstractmethod

class AnalyzerFormatter(ABC):
    @abstractmethod
    def format(self, stats: dict) -> None:
        pass