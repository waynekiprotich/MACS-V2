from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseEngine(ABC):
    """
    BaseEngine class with abstract methods execute_signal, get_positions, get_account_summary.
    """
    
    @abstractmethod
    def execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a given trading signal.
        Returns a dictionary representing the result of the execution.
        """
        pass
        
    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Retrieves a list of currently open positions.
        """
        pass
        
    @abstractmethod
    def get_account_summary(self) -> Dict[str, Any]:
        """
        Retrieves a summary of the account (balance, equity, etc.).
        """
        pass
