from abc import ABC, abstractmethod

class FinancialInstrument(ABC):
    """
    Abstract base class for all strategy-related instruments.
    """
    def __init__(self, **params):
        self.params = params
        
    @abstractmethod
    def price(self) -> float:
        pass

    @abstractmethod
    def greeks(self) -> dict:
        pass
